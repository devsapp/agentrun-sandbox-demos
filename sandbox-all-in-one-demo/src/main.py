"""
AI 对话管理服务

提供对话式 AI 代码生成和执行的 API
集成 AI 代码生成器和 Sandbox 执行器，提供完整的对话式代码生成和执行功能
"""

import asyncio
import json
import os
import re
import time
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Any

import httpx
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from ai_code_generator import ScraperCodeGenerator
from sandbox_executor import SandboxExecutor
from agentrun.sandbox import Sandbox, TemplateType

# 加载环境变量
load_dotenv()

# 读取环境变量
LOCAL_MODE = os.environ.get("LOCAL_MODE", "false").lower() == "true"

# 启动时打印模式信息
if LOCAL_MODE:
    print("=" * 70)
    print("[本地模式] 已启用")
    print("将直接调用 localhost:5000 的 API，绕过 30 秒超时限制")
    print("=" * 70)
else:
    print("=" * 70)
    print("[远程模式] 默认模式")
    print("将使用 AgentRun SDK 调用远程云服务")
    print("注意：远程模式有 30 秒执行限制")
    print("=" * 70)

# ============ FastAPI 应用 ============

app = FastAPI(
    title="AI Chat & Code Execution Server",
    description="对话式 AI 代码生成和执行服务",
    version="1.0.0",
)

# CORS 配置 - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录 - 使用 React 前端构建
    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend/dist")

if os.path.exists(FRONTEND_DIR):
    # 使用新的 React 前端
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")
    print(f"[OK] 前端已加载: {FRONTEND_DIR}")
else:
    print(f"[WARNING] 前端文件未找到: {FRONTEND_DIR}")
    print(f"   请运行: cd frontend && pnpm install && pnpm build")

# ============ 数据模型 ============


class SendMessageRequest(BaseModel):
    """发送消息请求"""

    session_id: str
    message: str


class ExecuteCodeRequest(BaseModel):
    """执行代码请求"""

    session_id: str
    message_id: str
    code: Optional[str] = None
    language: str = "javascript"  # 代码语言类型: 'javascript', 'shell', 'python'，默认为 javascript
    context_id: Optional[str] = None  # 执行标识符（预留参数）


# ============ 全局状态 ============

# 全局单会话 ID（固定）
GLOBAL_SESSION_ID = "global-session"

# 对话会话存储
# {session_id: {
#     "messages": [{"message_id": str, "role": str, "content": str, "code": str, "timestamp": float}],
#     "sandbox_id": str,
#     "sandbox": Sandbox,
#     "cdp_url": str,
#     "vnc_url": str,
#     "executor": SandboxExecutor,
#     "created_at": float,
#     "last_activity": float
# }}
chat_sessions: Dict[str, Dict] = {}

# WebSocket 连接池
# {session_id: [websocket, ...]}
chat_websockets: Dict[str, List[WebSocket]] = defaultdict(list)

# 日志 WebSocket 连接池
# {sandbox_id: [websocket, ...]}
log_websockets: Dict[str, List[WebSocket]] = defaultdict(list)

# Sandbox URL 存储（从 vncviewer/vnc_server.py 迁移）
# {sandbox_id: {"cdp_url": str, "vnc_url": str, "last_access_at": float}}
sandbox_urls: Dict[str, Dict] = {}

# 用户确认状态（用于等待用户点击"继续"）
# {sandbox_id: {"confirmed": bool, "event": asyncio.Event}}
user_confirmations: Dict[str, Dict] = {}

# AI 代码生成器（全局单例）
code_generator: Optional[ScraperCodeGenerator] = None

# VNC Server URL（用于推送日志）
VNC_SERVER_URL = os.getenv("VNC_SERVER_URL", "http://localhost:8181")

# ============ 辅助函数 ============


def get_code_generator() -> ScraperCodeGenerator:
    """
    获取代码生成器实例（懒加载）

    Returns:
        ScraperCodeGenerator 实例

    Raises:
        ValueError: 如果 API Key 未设置
    """
    global code_generator
    if code_generator is None:
        code_generator = ScraperCodeGenerator()
    return code_generator


def is_sandbox_alive(sandbox: Sandbox) -> bool:
    """
    检查 Sandbox 是否仍然有效
    
    Args:
        sandbox: Sandbox 实例
    
    Returns:
        bool: True 表示有效，False 表示已失效
    """
    try:
        # 尝试获取 sandbox 状态
        status = sandbox.status
            print(f"[检查] Sandbox 状态: {status}")
        # 状态可能是 "Running"、"RUNNING" 或 "READY"（不同版本 SDK）
        # READY 表示 Sandbox 已就绪且可以执行任务
        return status.upper() in ["RUNNING", "READY"]
    except Exception as e:
        print(f"[WARNING] Sandbox 状态检查失败: {e}")
        return False


async def cleanup_sandbox_resources(sandbox_id: str, session_id: Optional[str] = None):
    """
    清理 Sandbox 相关资源
    
    Args:
        sandbox_id: Sandbox ID
        session_id: Session ID（可选，如果提供则清理会话中的引用）
    """
    print(f"[清理] Sandbox 资源: {sandbox_id}")
    
    # 1. 清理日志 WebSocket
    if sandbox_id in log_websockets:
        connections = log_websockets[sandbox_id]
        for ws in connections:
            try:
                await ws.close()
            except:
                pass
        del log_websockets[sandbox_id]
        print(f"  [OK] 已清理 {len(connections)} 个日志 WebSocket")
    
    # 2. 清理会话中的 sandbox 引用
    if session_id and session_id in chat_sessions:
        chat_sessions[session_id].pop("sandbox", None)
        chat_sessions[session_id].pop("sandbox_id", None)
        chat_sessions[session_id].pop("sandbox_http_url", None)
        chat_sessions[session_id].pop("executor", None)
        print(f"  [OK] 已清理会话 {session_id} 中的 Sandbox 引用")


def create_or_get_sandbox(session_id: str) -> Dict[str, Any]:
    """
    创建或获取 Sandbox
    
    支持自动检测 Sandbox 状态并在失效时重建

    如果会话已有 Sandbox，检查其状态：
    - 如果有效，则复用
    - 如果失效，则清理并重新创建

    Args:
        session_id: 会话 ID

    Returns:
        {
            "sandbox_id": str,
            "sandbox": Sandbox,
            "cdp_url": str,
            "vnc_url": str,
            "executor": SandboxExecutor
        }

    Raises:
        ValueError: 如果无法解析 CDP URL
        Exception: 如果 Sandbox 创建失败
    """
    # 如果会话已有 Sandbox，检查是否仍然有效
    if session_id in chat_sessions and chat_sessions[session_id].get("sandbox"):
        sandbox = chat_sessions[session_id]["sandbox"]
        sandbox_id = chat_sessions[session_id]["sandbox_id"]
        
        # 检查 sandbox 是否仍然有效
        if is_sandbox_alive(sandbox):
            print(f"[复用] 现有 Sandbox: {sandbox_id}")
            return {
                "sandbox_id": sandbox_id,
                "sandbox": sandbox,
                "sandbox_http_url": chat_sessions[session_id].get("sandbox_http_url"),
                "cdp_url": chat_sessions[session_id]["cdp_url"],
                "vnc_url": chat_sessions[session_id]["vnc_url"],
                "executor": chat_sessions[session_id]["executor"],
            }
        else:
            # Sandbox 已失效，清理旧数据
            print(f"[WARNING] Sandbox 已失效，准备重新创建: {sandbox_id}")
            
            # 清理会话中的 sandbox 信息
            chat_sessions[session_id].pop("sandbox", None)
            chat_sessions[session_id].pop("sandbox_id", None)
            chat_sessions[session_id].pop("sandbox_http_url", None)
            chat_sessions[session_id].pop("executor", None)
            
            # 清理日志 websocket
            if sandbox_id in log_websockets:
                connections = log_websockets[sandbox_id]
                print(f"  [清理] {len(connections)} 个日志 WebSocket")
                del log_websockets[sandbox_id]
            
            # 继续创建新 sandbox（下面的代码）
            print(f"[创建] 开始创建新的 Sandbox...")

    # 创建新 Sandbox
    template_name = os.getenv("AIO_TEMPLATE_NAME", "your-aio-template")

    print(f"[配置] 创建 Sandbox:")
    print(f"  - 模板: {template_name}")
    print(f"  - 超时: 1800 秒")
    print(f"  - OSS 挂载: [] (已覆盖模板配置)")
    print(f"  - NAS 挂载: None (已禁用)")
    
    sandbox = Sandbox.create(
        template_type=TemplateType.AIO,
        template_name=template_name,
        sandbox_idle_timeout_seconds=1800,  # 30 分钟超时
    )

    sandbox_id = sandbox.sandbox_id
    
    # 获取 CDP URL（用于提取正确的域名）
    try:
        cdp_url = sandbox.get_cdp_url() if hasattr(sandbox, 'get_cdp_url') else None
    except Exception as e:
        print(f"获取 CDP URL 失败: {e}")
        cdp_url = None
    
    # 根据 LOCAL_MODE 返回不同的 URL
    if LOCAL_MODE:
        # 本地模式：使用 localhost:5000
        cdp_url = "ws://localhost:5000/ws/automation"
        vnc_url = "ws://localhost:5000/ws/liveview"
        print(f"[本地] CDP URL: {cdp_url}")
        print(f"[本地] VNC URL: {vnc_url}")
    else:
        # 远程模式：使用实际的远程 URL
        if not cdp_url:
            cdp_url = "ws://localhost:5000/ws/automation"  # Fallback
        vnc_url = sandbox.get_vnc_url()

    # 从 CDP URL 提取正确的 HTTP URL
    import re
    sandbox_http_url = None
    
    if LOCAL_MODE:
        # 本地模式：直接使用 localhost:5000
        sandbox_http_url = "http://localhost:5000"
        print(f"[本地] HTTP URL: {sandbox_http_url}")
    elif cdp_url and cdp_url.startswith('ws'):
        # 远程模式：从 CDP URL 提取域名
        match = re.search(r'wss?://(.+?)/sandboxes/(.+?)/', cdp_url)
        if match:
            domain = match.group(1)
            sid = match.group(2)
            sandbox_http_url = f"https://{domain}/sandboxes/{sid}"
            print(f"[OK] 提取 Sandbox HTTP URL: {sandbox_http_url}")
    
    # 如果提取失败，使用默认格式（但会失败）
    if not sandbox_http_url:
        print(f"[WARNING] 无法从 CDP URL 提取域名，使用默认格式")
        sandbox_http_url = f"https://agentrun-data.cn-hangzhou.aliyuncs.com/sandboxes/{sandbox_id}"
        print(f"[默认] 使用默认 URL: {sandbox_http_url}")

    # 创建执行器（传入 sandbox 实例用于 context.execute_async）
    executor = SandboxExecutor(sandbox_http_url, sandbox=sandbox)

    # 保存到会话
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "created_at": time.time(),
        }

    chat_sessions[session_id].update(
        {
            "sandbox_id": sandbox_id,
            "sandbox": sandbox,
            "sandbox_http_url": sandbox_http_url,  # 保存基础 URL
            "cdp_url": cdp_url,
            "vnc_url": vnc_url,
            "executor": executor,
            "last_activity": time.time(),
        }
    )

    # 不再需要注册到外部 VNC Server，使用内置 WebSocket
    print(f"[OK] Sandbox 创建成功: {sandbox_id}")
    print(f"[日志] WebSocket: ws://localhost:8181/ws/log/{sandbox_id}")

    return {
        "sandbox_id": sandbox_id,
        "sandbox": sandbox,
        "sandbox_http_url": sandbox_http_url,  # 返回基础 URL
        "cdp_url": cdp_url,
        "vnc_url": vnc_url,
        "executor": executor,
    }


async def push_log_to_vnc(sandbox_id: str, level: str, message: str):
    """
    推送日志到连接的 WebSocket 客户端
    
    Args:
        sandbox_id: Sandbox ID
        level: 日志级别（INFO, WARNING, ERROR, THINKING, ACTION, RESULT）
        message: 日志消息
    """
    # 添加调试信息
    print(f"[DEBUG] push_log_to_vnc called: sandbox_id={sandbox_id}, level={level}, connections={len(log_websockets.get(sandbox_id, []))}")
    
    if sandbox_id not in log_websockets or not log_websockets[sandbox_id]:
        # 没有 WebSocket 连接，静默跳过
        print(f"[DEBUG] No WebSocket connections for sandbox {sandbox_id}")
        return
    
    log_data = {
        "type": "log",
        "level": level,
        "message": message,
        "timestamp": time.time()
    }
    
    # 向所有连接的客户端广播日志
    disconnected = []
    for ws in log_websockets[sandbox_id]:
        try:
            await ws.send_json(log_data)
            print(f"[DEBUG] Log sent successfully to WebSocket")
        except Exception as e:
            print(f"[DEBUG] Failed to send log to WebSocket: {e}")
            disconnected.append(ws)
    
    # 移除断开的连接
    for ws in disconnected:
        log_websockets[sandbox_id].remove(ws)


async def broadcast_to_session(session_id: str, message: Dict[str, Any]):
    """
    广播消息到会话的所有 WebSocket 连接

    Args:
        session_id: 会话 ID
        message: 要广播的消息（字典）
    """
    print(f"[广播] broadcast_to_session 被调用")
    print(f"   会话ID: {session_id}")
    print(f"   消息类型: {message.get('type')}")
    print(f"   当前 chat_websockets 中的会话: {list(chat_websockets.keys())}")
    
    if session_id in chat_websockets:
        ws_count = len(chat_websockets[session_id])
        print(f"   找到 {ws_count} 个 WebSocket 连接")
        for i, ws in enumerate(list(chat_websockets[session_id])):
            try:
                await ws.send_json(message)
                print(f"   [OK] 消息已发送到 WebSocket #{i+1}")
            except Exception as e:
                print(f"   ✗ WebSocket #{i+1} 发送失败: {e}")
                # WebSocket 已关闭，移除
                chat_websockets[session_id].remove(ws)
    else:
        print(f"   [WARNING] 会话 {session_id} 没有活跃的 WebSocket 连接")



# ============ API 端点 ============


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    根目录，返回对话界面

    Returns:
        HTML 响应（chat.html 或默认页面）
    """
    html_path = os.path.join(FRONTEND_DIR, "chat.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1>AI Chat Server</h1><p>前端文件未找到，请运行: cd frontend && pnpm build</p>"
    )


@app.post("/api/sandbox/create")
async def create_sandbox_endpoint(request: Request):
    """
     创建 Sandbox（用于 Playground）
    
    Args:
        request: 请求体
            - session_id: 会话 ID
    
    Returns:
        {
            "session_id": str,
            "sandbox_id": str,
            "vnc_url": str,
            "status": "created"
        }
    """
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id")
    
    # 创建会话（如果不存在）
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "created_at": time.time(),
        }
    
    try:
        # 创建或获取 Sandbox
        sandbox_info = create_or_get_sandbox(session_id)
        sandbox_id = sandbox_info["sandbox_id"]
        vnc_url = sandbox_info["vnc_url"]
        cdp_url = sandbox_info.get("cdp_url")
        sandbox_http_url = sandbox_info.get("sandbox_http_url")  #  获取基础 URL
        
        # 推送日志
        await push_log_to_vnc(sandbox_id, "INFO", "[Sandbox] Sandbox 已创建")
        await push_log_to_vnc(sandbox_id, "ACTION", f"[OK] Sandbox ID: {sandbox_id}")
        
        return {
            "sandbox_id": sandbox_id,
            "base_url": sandbox_http_url,  #  返回基础 URL
            "cdp_url": cdp_url,
            "vnc_url": vnc_url,
            "last_access_at": time.time(),
            "log_count": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建 Sandbox 失败: {str(e)}")


@app.get("/api/session/global")
async def get_global_session():
    """
    获取全局会话信息
    
    Returns:
        {
            "session_id": str,
            "sandbox_id": str or None,
            "base_url": str or None,
            "vnc_url": str or None,
            "cdp_url": str or None,
            "created_at": float,
            "message_count": int
        }
    """
    # 确保全局会话存在
    if GLOBAL_SESSION_ID not in chat_sessions:
        chat_sessions[GLOBAL_SESSION_ID] = {
            "messages": [],
            "created_at": time.time(),
            "last_activity": time.time(),
        }
    
    session = chat_sessions[GLOBAL_SESSION_ID]
    
    return {
        "session_id": GLOBAL_SESSION_ID,
        "sandbox_id": session.get("sandbox_id"),
        "base_url": session.get("sandbox_http_url"),  #  返回 base_url
        "vnc_url": session.get("vnc_url"),
        "cdp_url": session.get("cdp_url"),
        "created_at": session.get("created_at"),
        "message_count": len(session.get("messages", [])),
    }


@app.post("/api/session/rebuild")
async def rebuild_session():
    """
    重建全局会话
    
    清空消息历史、关闭旧 Sandbox、创建新 Sandbox
    
    Returns:
        {
            "session_id": str,
            "sandbox_id": str,
            "base_url": str,
            "vnc_url": str,
            "cdp_url": str,
            "status": "rebuilt"
        }
    """
    print(f"[刷新] 开始重建全局会话...")
    
    # 1. 清理旧 Sandbox（如果存在）
    if GLOBAL_SESSION_ID in chat_sessions:
        old_session = chat_sessions[GLOBAL_SESSION_ID]
        old_sandbox_id = old_session.get("sandbox_id")
        
        if old_sandbox_id:
            print(f"   清理旧 Sandbox: {old_sandbox_id}")
            await cleanup_sandbox_resources(old_sandbox_id, GLOBAL_SESSION_ID)
    
    # 2. 重置会话数据
    chat_sessions[GLOBAL_SESSION_ID] = {
        "messages": [],
        "created_at": time.time(),
        "last_activity": time.time(),
    }
    
    # 3. 创建新 Sandbox
    try:
        sandbox_info = create_or_get_sandbox(GLOBAL_SESSION_ID)
        sandbox_id = sandbox_info["sandbox_id"]
        sandbox_http_url = sandbox_info.get("sandbox_http_url")  #  获取 base_url
        vnc_url = sandbox_info["vnc_url"]
        cdp_url = sandbox_info.get("cdp_url")
        
        print(f"[OK] 全局会话已重建")
        print(f"   新 Sandbox ID: {sandbox_id}")
        
        # 推送日志
        await push_log_to_vnc(sandbox_id, "INFO", "[刷新] 会话已重建")
        await push_log_to_vnc(sandbox_id, "ACTION", f"[OK] 新 Sandbox: {sandbox_id[:20]}...")
        
        # 广播会话重建消息
        await broadcast_to_session(GLOBAL_SESSION_ID, {
            "type": "session_rebuilt",
            "data": {
                "session_id": GLOBAL_SESSION_ID,
                "sandbox_id": sandbox_id,
                "timestamp": time.time()
            }
        })
        
        return {
            "session_id": GLOBAL_SESSION_ID,
            "sandbox_id": sandbox_id,
            "base_url": sandbox_http_url,  #  返回 base_url
            "vnc_url": vnc_url,
            "cdp_url": cdp_url,
            "status": "rebuilt"
        }
    except Exception as e:
        print(f"[ERROR] 重建会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"重建会话失败: {str(e)}")


@app.post("/api/chat/send")
async def send_message(request: SendMessageRequest):
    """
    发送消息，AI 生成代码

    Args:
        request: 发送消息请求
            - session_id: 会话 ID
            - message: 用户消息

    Returns:
        {
            "session_id": str,
            "message_id": str,
            "role": "assistant",
            "content": str,  # AI 响应说明
            "code": str,  # 生成的代码
            "language": "python",
            "timestamp": float
        }
    """
    session_id = request.session_id
    user_message = request.message

    # 创建会话（如果不存在）
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "created_at": time.time(),
        }

    # 保存用户消息
    user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    user_msg = {
        "message_id": user_msg_id,
        "role": "user",
        "content": user_message,
        "timestamp": time.time(),
    }
    chat_sessions[session_id]["messages"].append(user_msg)
    chat_sessions[session_id]["last_activity"] = time.time()

    # 广播用户消息
    await broadcast_to_session(session_id, {"type": "message", "data": user_msg})

    # 创建或获取 Sandbox
    try:
        sandbox_info = create_or_get_sandbox(session_id)
        cdp_url = sandbox_info["cdp_url"]
        sandbox_id = sandbox_info["sandbox_id"]
        
        #  推送用户消息到日志
        await push_log_to_vnc(sandbox_id, "INFO", f"[用户] 用户: {user_message}")
    except Exception as e:
        error_msg = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": "assistant",
            "content": f"[ERROR] 创建 Sandbox 失败: {str(e)}",
            "timestamp": time.time(),
        }
        chat_sessions[session_id]["messages"].append(error_msg)
        await broadcast_to_session(session_id, {"type": "message", "data": error_msg})
        return error_msg

    # 推送日志到 VNC
    await push_log_to_vnc(sandbox_id, "THINKING", f"用户需求: {user_message}")
    await push_log_to_vnc(sandbox_id, "THINKING", "AI 正在生成代码...")

    # 调用 AI 生成代码
    try:
        generator = get_code_generator()

        # 提取对话历史（排除当前消息）
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in chat_sessions[session_id]["messages"]
            if msg["role"] in ["user", "assistant"]
        ]

        result = generator.generate_scraper_code(
            user_requirement=user_message,
            cdp_url=cdp_url,
            conversation_history=conversation_history[:-1],  # 排除当前消息
        )

        code = result["code"]
        explanation = result["explanation"]
        language = result.get("language", "javascript")  #  获取 AI 返回的语言类型
        
        #  将完整响应（包含所有步骤）作为 content
        # AI 可能返回多个代码块，需要保留完整内容用于前端解析
        full_content = result.get("full_response", f"{code}\n\n{explanation}")

        # 保存 AI 响应
        ai_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        
        ai_msg = {
            "message_id": ai_msg_id,
            "role": "assistant",
            "content": full_content,  #  使用完整响应，包含所有步骤
            "code": code,  # 保留向后兼容
            "language": language,  #  使用 AI 返回的语言类型
            "timestamp": time.time(),
        }
        chat_sessions[session_id]["messages"].append(ai_msg)

        #  推送 AI 响应摘要到日志（不推送完整代码，太长）
        await push_log_to_vnc(sandbox_id, "INFO", f"[AI] AI: 代码已生成")
        await push_log_to_vnc(sandbox_id, "ACTION", "[OK] 代码生成完成")

        # 广播 AI 响应
        await broadcast_to_session(session_id, {"type": "message", "data": ai_msg})

        return ai_msg

    except Exception as e:
        error_msg = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": "assistant",
            "content": f"[ERROR] 代码生成失败: {str(e)}",
            "timestamp": time.time(),
        }
        chat_sessions[session_id]["messages"].append(error_msg)

        await push_log_to_vnc(sandbox_id, "ERROR", f"代码生成失败: {str(e)}")

        await broadcast_to_session(session_id, {"type": "message", "data": error_msg})

        return error_msg


@app.post("/api/chat/execute")
async def execute_code(request: ExecuteCodeRequest):
    """
    执行代码

    Args:
        request: 执行代码请求
            - session_id: 会话 ID
            - message_id: 包含代码的消息 ID

    Returns:
        {
            "session_id": str,
            "execution_id": str,
            "status": "running",
            "sandbox_id": str
        }

    Raises:
        HTTPException: 如果会话不存在或消息不包含代码
    """
    session_id = request.session_id
    message_id = request.message_id
    context_id = request.context_id  # 执行标识符（预留参数）

    # 检查会话是否存在，不存在则创建
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "created_at": time.time(),
        }

    #  优先使用请求中的代码（支持 Playground）
    if request.code:
        code = request.code
    else:
        # 查找消息中的代码
        message = None
        for msg in chat_sessions[session_id]["messages"]:
            if msg["message_id"] == message_id:
                message = msg
                break

        if not message or "code" not in message:
            raise HTTPException(status_code=404, detail="消息不存在或不包含代码")
        
        code = message["code"]

    # 获取 Sandbox 和执行器
    sandbox_info = create_or_get_sandbox(session_id)
    executor = sandbox_info["executor"]
    sandbox_id = sandbox_info["sandbox_id"]

    # 生成执行 ID
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"
    
    # 记录执行标识符
    if context_id:
        print(f"📌 执行标识符: {context_id}")

    # 推送日志
    await push_log_to_vnc(sandbox_id, "ACTION", "[执行] 开始执行代码...")

    # 广播执行开始
    await broadcast_to_session(
        session_id,
        {
            "type": "execution_start",
            "data": {
                "execution_id": execution_id,
                "message_id": message_id,
                "sandbox_id": sandbox_id,
            },
        },
    )

    # 异步执行代码
    async def run_code():
        """异步执行代码的内部函数"""
        try:
            #  设置日志回调函数（用于将 SandboxExecutor 的日志实时推送到前端）
            def executor_log_callback(message: str, level: str = "INFO"):
                """
                SandboxExecutor 日志回调 - 异步推送日志
                """
                try:
                    #  使用 asyncio.create_task 创建任务
                    # 注意：这在同步函数中调用，需要确保有事件循环
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        # 在运行的事件循环中创建任务
                        loop.create_task(push_log_to_vnc(sandbox_id, level, message))
                    except RuntimeError:
                        # 如果没有运行的事件循环，使用 ensure_future
                        asyncio.ensure_future(push_log_to_vnc(sandbox_id, level, message))
                except Exception as e:
                    print(f"[WARNING]  推送 SandboxExecutor 日志失败: {e}")
            
            # 动态设置回调
            executor.set_log_callback(executor_log_callback)
            
            # 开始执行代码
            await push_log_to_vnc(sandbox_id, "ACTION", "[执行] 开始执行代码...")

            #  使用显式的 language 参数
            language = request.language
            print(f"[OK] 语言类型: {language}")
            
            # 根据语言类型执行代码
            if language == 'shell':
                # 直接执行 Shell 命令（通过 /processes/cmd）
                await push_log_to_vnc(sandbox_id, "INFO", f"[配置] Shell 命令，通过 /processes/cmd 执行")
                exec_result = executor.execute_shell_command(code.strip())
                
                # 转换为统一格式
                if 'result' in exec_result:
                    cmd_result = exec_result['result']
                    exec_result = {
                        "executionId": context_id or "shell_exec",
                        "status": "completed" if cmd_result.get('exitCode', -1) == 0 else "failed",
                        "result": cmd_result
                    }
            elif language == 'javascript':
                # [配置] 执行 Node.js 代码（使用 SDK Context API）
                await push_log_to_vnc(sandbox_id, "INFO", f"[OK] Node.js 代码，使用 javascript 执行器")
                
                # 定义输出回调函数
                async def on_streaming_output(line: str, stream_type: str):
                    """实时推送流式输出到 VNC Viewer"""
                    if stream_type == "error":
                        await push_log_to_vnc(sandbox_id, "ERROR", line.strip() if line.strip() else line)
                    elif stream_type == "info":
                        await push_log_to_vnc(sandbox_id, "INFO", line.strip() if line.strip() else line)
                    else:
                        # stdout/stderr 输出
                        if line.strip():
                            await push_log_to_vnc(sandbox_id, "STDOUT", line.strip())
                
                # 使用 SDK 执行 Node.js 代码
                exec_result = await executor.execute_nodejs_code_streaming(
                    code=code,
                    on_output=on_streaming_output
                )
            else:
                # [配置] 执行 Python 代码（使用 SDK Context API）
                await push_log_to_vnc(sandbox_id, "INFO", f"🐍 Python 代码，使用 python 执行器")
                
                # 定义输出回调函数
                async def on_streaming_output(line: str, stream_type: str):
                    """实时推送流式输出到 VNC Viewer"""
                    if stream_type == "error":
                        await push_log_to_vnc(sandbox_id, "ERROR", line.strip() if line.strip() else line)
                    elif stream_type == "info":
                        await push_log_to_vnc(sandbox_id, "INFO", line.strip() if line.strip() else line)
                    else:
                        # stdout/stderr 输出
                        if line.strip():
                            await push_log_to_vnc(sandbox_id, "STDOUT", line.strip())
                
                # 使用 SDK 执行（不传 context_id，让 SDK 自动创建）
                exec_result = await executor.execute_python_code_streaming(
                    code=code,
                    context_id=None,  # 不传 context_id，让 SDK 自动创建
                    on_output=on_streaming_output
                )

            
            #  返回执行结果（包含 executionId）
            return_result = exec_result

            # 推送执行日志
            if exec_result["status"] == "completed":
                stdout = exec_result["result"].get("stdout", "")
                stderr = exec_result["result"].get("stderr", "")

                # 注意：流式执行已经实时推送了输出，这里不需要再推送 stdout
                # 只需要推送 stderr（如果有的话）和完成消息
                if stderr:
                    await push_log_to_vnc(sandbox_id, "STDERR", f"[WARNING]  标准错误:\n{stderr}")

                # 推送执行完成消息
                await push_log_to_vnc(sandbox_id, "RESULT", "[OK] 执行完成")

                #  广播真正的 Sandbox contextId
                real_context_id = exec_result.get("executionId", execution_id)
                
                print(f"[通知] 准备广播 execution_complete 到会话 {session_id}")
                print(f"   执行ID: {execution_id}")
                print(f"   Context ID: {real_context_id}")
                print(f"   状态: success")
                
                await broadcast_to_session(
                    session_id,
                    {
                        "type": "execution_complete",
                        "data": {
                            "execution_id": execution_id,
                            "context_id": real_context_id,  #  返回真正的 Sandbox contextId
                            "status": "success",
                            "stdout": stdout,
                            "stderr": stderr,
                        },
                    },
                )
                
                print(f"[OK] execution_complete 消息已广播")
            else:
                #  广播真正的 Sandbox contextId
                real_context_id = exec_result.get("executionId", execution_id)
                
                stderr = exec_result["result"].get("stderr", "Unknown error")
                #  推送完整的错误信息到日志
                await push_log_to_vnc(sandbox_id, "ERROR", f"[ERROR] 执行失败:\n{stderr}")

                await broadcast_to_session(
                    session_id,
                    {
                        "type": "execution_complete",
                        "data": {
                            "execution_id": execution_id,
                            "context_id": real_context_id,  #  返回真正的 Sandbox contextId
                            "status": "failed",
                            "error": stderr,
                        },
                    },
                )
            
            #  返回执行结果
            return return_result

        except Exception as e:
            await push_log_to_vnc(sandbox_id, "ERROR", f"[ERROR] 执行过程出错: {str(e)}")

            await broadcast_to_session(
                session_id,
                {
                    "type": "execution_complete",
                    "data": {
                        "execution_id": execution_id,
                        "status": "error",
                        "error": str(e),
                    },
                },
            )

            #  返回 None 表示执行失败
            return None

    #  同步执行代码并等待结果，以便返回真正的 context_id
    exec_result = await run_code()
    
    # 从执行结果中获取真正的 Sandbox contextId
    real_context_id = exec_result.get("executionId") if exec_result else execution_id

    return {
        "session_id": session_id,
        "execution_id": execution_id,
        "context_id": real_context_id,  #  返回真正的 Sandbox contextId
        "status": "running",
        "sandbox_id": sandbox_id,
    }


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    获取对话历史

    Args:
        session_id: 会话 ID

    Returns:
        {
            "session_id": str,
            "messages": List[Dict],  # 消息列表
            "sandbox_id": str or None,
            "cdp_url": str or None,
            "vnc_url": str or None,
            "created_at": float,
            "last_activity": float or None
        }

    Raises:
        HTTPException: 如果会话不存在
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = chat_sessions[session_id]

    return {
        "session_id": session_id,
        "messages": session["messages"],
        "sandbox_id": session.get("sandbox_id"),
        "cdp_url": session.get("cdp_url"),
        "vnc_url": session.get("vnc_url"),
        "created_at": session["created_at"],
        "last_activity": session.get("last_activity"),
    }


async def process_user_message(session_id: str, user_message: str):
    """
    异步处理用户消息，生成代码并执行
    
    Args:
        session_id: 会话 ID
        user_message: 用户消息内容
    """
    try:
        # 创建或获取 Sandbox
        try:
            sandbox_info = create_or_get_sandbox(session_id)
            cdp_url = sandbox_info["cdp_url"]
            sandbox_id = sandbox_info["sandbox_id"]
            executor = sandbox_info["executor"]
            
            # 推送用户消息到日志
            await push_log_to_vnc(sandbox_id, "INFO", f"[用户] 用户: {user_message}")
        except Exception as e:
            error_msg = {
                "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "assistant",
                "content": f"[ERROR] 创建 Sandbox 失败: {str(e)}",
                "timestamp": time.time(),
            }
            chat_sessions[session_id]["messages"].append(error_msg)
            await broadcast_to_session(session_id, {"type": "message", "data": error_msg})
            return

        # 推送日志到 VNC
        await push_log_to_vnc(sandbox_id, "THINKING", f"用户需求: {user_message}")
        await push_log_to_vnc(sandbox_id, "THINKING", "AI 正在生成代码...")

        # 调用 AI 生成代码
        try:
            generator = get_code_generator()

            # 提取对话历史（排除当前消息）
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in chat_sessions[session_id]["messages"]
                if msg["role"] in ["user", "assistant"]
            ]

            result = generator.generate_scraper_code(
                user_requirement=user_message,
                cdp_url=cdp_url,
                conversation_history=conversation_history[:-1],  # 排除当前消息
            )

            code = result["code"]
            explanation = result["explanation"]
            language = result.get("language", "javascript")  #  获取 AI 返回的语言类型
            
            # 将完整响应（包含所有步骤）作为 content
            full_content = result.get("full_response", f"{code}\n\n{explanation}")

            # 保存 AI 响应
            ai_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
            
            ai_msg = {
                "message_id": ai_msg_id,
                "role": "assistant",
                "content": full_content,
                "code": code,
                "language": language,  #  使用 AI 返回的语言类型
                "timestamp": time.time(),
            }
            chat_sessions[session_id]["messages"].append(ai_msg)

            # 推送 AI 消息
            await broadcast_to_session(session_id, {"type": "message", "data": ai_msg})
            await push_log_to_vnc(sandbox_id, "SUCCESS", "[OK] 代码已生成，请在前端点击执行按钮运行代码")
            await push_log_to_vnc(sandbox_id, "INFO", "[提示] 提示：你可以编辑代码后再执行")

        except Exception as e:
            error_msg = {
                "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "assistant",
                "content": f"[ERROR] 生成代码失败: {str(e)}",
                "timestamp": time.time(),
            }
            chat_sessions[session_id]["messages"].append(error_msg)
            await broadcast_to_session(session_id, {"type": "message", "data": error_msg})
            await push_log_to_vnc(sandbox_id, "ERROR", f"[ERROR] 错误: {str(e)}")
            
    except Exception as e:
        print(f"[process_user_message] 错误: {e}")
        import traceback
        traceback.print_exc()


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket 实时消息推送和接收

    推送消息类型：
    - {"type": "message", "data": {...}}  # 新消息
    - {"type": "execution_start", "data": {...}}  # 开始执行
    - {"type": "execution_complete", "data": {...}}  # 执行完成

    接收消息类型：
    - {"type": "message", "content": "..."}  # 用户发送的消息

    Args:
        websocket: WebSocket 连接
        session_id: 会话 ID
    """
    await websocket.accept()
    chat_websockets[session_id].append(websocket)

    print(
        f"WebSocket connected for session {session_id}. Total: {len(chat_websockets[session_id])}"
    )

    try:
        # 发送历史消息
        if session_id in chat_sessions:
            for msg in chat_sessions[session_id]["messages"]:
                await websocket.send_json({"type": "message", "data": msg})

        # 接收并处理消息
        while True:
            # 接收消息
            data = await websocket.receive_json()
            print(f"[WebSocket] 收到消息: {data}")
            
            # 处理消息
            if data.get("type") == "message":
                user_message = data.get("content", "")
                if not user_message.strip():
                    continue
                
                # 创建会话（如果不存在）
                if session_id not in chat_sessions:
                    chat_sessions[session_id] = {
                        "messages": [],
                        "created_at": time.time(),
                    }

                # 保存用户消息
                user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
                user_msg = {
                    "message_id": user_msg_id,
                    "role": "user",
                    "content": user_message,
                    "timestamp": time.time(),
                }
                chat_sessions[session_id]["messages"].append(user_msg)
                chat_sessions[session_id]["last_activity"] = time.time()

                # 广播用户消息
                await broadcast_to_session(session_id, {"type": "message", "data": user_msg})

                # 异步处理消息（避免阻塞 WebSocket）
                asyncio.create_task(process_user_message(session_id, user_message))
                
    except WebSocketDisconnect:
        chat_websockets[session_id].remove(websocket)
        print(
            f"WebSocket disconnected for session {session_id}. Remaining: {len(chat_websockets[session_id])}"
        )
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        if websocket in chat_websockets[session_id]:
            chat_websockets[session_id].remove(websocket)


@app.websocket("/ws/log/{sandbox_id}")
async def websocket_log_endpoint(websocket: WebSocket, sandbox_id: str):
    """
    WebSocket 日志推送
    
    推送消息类型：
    - {"type": "log", "level": "INFO", "message": "...", "timestamp": 123456.789}
    
    Args:
        websocket: WebSocket 连接
        sandbox_id: Sandbox ID
    """
    await websocket.accept()
    log_websockets[sandbox_id].append(websocket)
    
    print(f"[OK] Log WebSocket connected for sandbox {sandbox_id}. Total: {len(log_websockets[sandbox_id])}")
    print(f"[DEBUG] Current log_websockets keys: {list(log_websockets.keys())}")
    
    #  发送连接成功消息
    await websocket.send_json({
        "type": "log",
        "level": "INFO",
        "message": f"[广播] 日志 WebSocket 已连接 (Sandbox: {sandbox_id[:20]}...)",
        "timestamp": time.time()
    })
    
    try:
        # 保持连接，接收心跳
        while True:
            data = await websocket.receive_text()
            print(f"[DEBUG] Received heartbeat from log WebSocket: {data}")
    except WebSocketDisconnect:
        log_websockets[sandbox_id].remove(websocket)
        print(f"[WARNING]  Log WebSocket disconnected for sandbox {sandbox_id}. Remaining: {len(log_websockets[sandbox_id])}")
    except Exception as e:
        print(f"[ERROR] Log WebSocket error for sandbox {sandbox_id}: {e}")
        import traceback
        traceback.print_exc()
        if websocket in log_websockets[sandbox_id]:
            log_websockets[sandbox_id].remove(websocket)


# ============ Sandbox URL 管理 API（从 vncviewer/vnc_server.py 迁移）============

class URLInfo(BaseModel):
    """URL 信息"""
    cdp_url: Optional[str] = None
    vnc_url: Optional[str] = None


@app.get("/api/sandboxes")
async def list_sandboxes():
    """
    获取所有活跃的 Sandbox 列表
    
    Returns:
        [
            {
                "sandbox_id": str,
                "cdp_url": str or null,
                "vnc_url": str or null,
                "last_access_at": float
            },
            ...
        ]
    """
    result = []
    for sandbox_id, data in sandbox_urls.items():
        result.append({
            "sandbox_id": sandbox_id,
            "cdp_url": data.get("cdp_url"),
            "vnc_url": data.get("vnc_url"),
            "last_access_at": data.get("last_access_at"),
        })
    return result


@app.get("/api/sandboxes/{sandbox_id}")
async def get_sandbox_info(sandbox_id: str):
    """
    获取指定 Sandbox 的信息
    
    Returns:
        {
            "sandbox_id": str,
            "cdp_url": str or null,
            "vnc_url": str or null,
            "last_access_at": float
        }
    """
    if sandbox_id not in sandbox_urls:
        # 不抛出 404，返回空信息（允许查询未设置 URL 的 Sandbox）
        return {
            "sandbox_id": sandbox_id,
            "cdp_url": None,
            "vnc_url": None,
            "last_access_at": None,
        }
    
    data = sandbox_urls[sandbox_id]
    data["last_access_at"] = time.time()
    
    return {
        "sandbox_id": sandbox_id,
        "cdp_url": data.get("cdp_url"),
        "vnc_url": data.get("vnc_url"),
        "last_access_at": data.get("last_access_at"),
    }


@app.delete("/api/sandbox/{sandbox_id}")
async def delete_sandbox(sandbox_id: str):
    """
    删除指定的 Sandbox
    
    清理与该 Sandbox 相关的所有数据：
    - sandbox_urls（CDP/VNC URL）
    - log_websockets（日志 WebSocket 连接）
    - user_confirmations（用户确认状态）
    - chat_sessions 中的关联
    
    Returns:
        {
            "sandbox_id": str,
            "status": "deleted"
        }
    """
    print(f"[删除]  删除 Sandbox: {sandbox_id}")
    
    # 1. 清理 sandbox_urls
    if sandbox_id in sandbox_urls:
        del sandbox_urls[sandbox_id]
        print(f"   [完成] 已清理 sandbox_urls")
    
    # 2. 关闭并清理日志 WebSocket 连接
    if sandbox_id in log_websockets:
        connections = log_websockets[sandbox_id]
        for ws in connections:
            try:
                await ws.close()
            except Exception as e:
                print(f"   [WARNING]  关闭 WebSocket 失败: {e}")
        del log_websockets[sandbox_id]
        print(f"   [完成] 已清理 {len(connections)} 个日志 WebSocket 连接")
    
    # 3. 清理用户确认状态
    if sandbox_id in user_confirmations:
        del user_confirmations[sandbox_id]
        print(f"   [完成] 已清理 user_confirmations")
    
    # 4. 清理关联的会话中的 sandbox_id
    cleaned_sessions = 0
    for session_id, session_data in chat_sessions.items():
        if session_data.get("sandbox_id") == sandbox_id:
            session_data["sandbox_id"] = None
            cleaned_sessions += 1
    if cleaned_sessions > 0:
        print(f"   [完成] 已清理 {cleaned_sessions} 个会话的 sandbox_id 关联")
    
    print(f"[OK] Sandbox {sandbox_id} 已删除")
    
    return {
        "sandbox_id": sandbox_id,
        "status": "deleted"
    }



@app.post("/api/sandboxes/{sandbox_id}/cdp")
async def set_cdp_url(sandbox_id: str, info: URLInfo):
    """
    设置 CDP URL（自动创建记录）
    
    Body:
        {
            "cdp_url": "wss://..."
        }
    """
    if sandbox_id not in sandbox_urls:
        # 自动创建记录
        sandbox_urls[sandbox_id] = {
            "cdp_url": None,
            "vnc_url": None,
            "last_access_at": time.time(),
        }
    
    sandbox_urls[sandbox_id]["cdp_url"] = info.cdp_url
    sandbox_urls[sandbox_id]["last_access_at"] = time.time()
    
    return {"sandbox_id": sandbox_id, "cdp_url": info.cdp_url}


@app.post("/api/sandboxes/{sandbox_id}/vnc")
async def set_vnc_url(sandbox_id: str, info: URLInfo):
    """
    设置 VNC URL（自动创建记录）
    
    Body:
        {
            "vnc_url": "wss://..."
        }
    """
    if sandbox_id not in sandbox_urls:
        # 自动创建记录
        sandbox_urls[sandbox_id] = {
            "cdp_url": None,
            "vnc_url": None,
            "last_access_at": time.time(),
        }
    
    sandbox_urls[sandbox_id]["vnc_url"] = info.vnc_url
    sandbox_urls[sandbox_id]["last_access_at"] = time.time()
    
    return {"sandbox_id": sandbox_id, "vnc_url": info.vnc_url}


@app.get("/api/sandboxes/{sandbox_id}/cdp")
async def get_cdp_url(sandbox_id: str):
    """获取 CDP URL"""
    return {"cdp_url": sandbox_urls.get(sandbox_id, {}).get("cdp_url")}


@app.get("/api/sandboxes/{sandbox_id}/vnc")
async def get_vnc_url(sandbox_id: str):
    """获取 VNC URL"""
    return {"vnc_url": sandbox_urls.get(sandbox_id, {}).get("vnc_url")}


# ============ 日志 API（从 vncviewer/vnc_server.py 迁移）============

class LogEntry(BaseModel):
    """日志条目"""
    level: str
    message: str
    extra: Optional[Dict] = None


@app.post("/api/log/{sandbox_id}", status_code=201)
async def write_log(sandbox_id: str, log_entry: LogEntry):
    """
    写入日志
    
    Body:
        {
            "level": "INFO",
            "message": "日志内容",
            "extra": {"key": "value"}  // 可选
        }
    """
    # 推送日志到 WebSocket 客户端
    await push_log_to_vnc(
        sandbox_id=sandbox_id,
        level=log_entry.level,
        message=log_entry.message,
        extra=log_entry.extra
    )
    
    return {"sandbox_id": sandbox_id}


# ============ 用户确认 API（从 vncviewer/vnc_server.py 迁移）============

@app.post("/api/sandboxes/{sandbox_id}/confirm")
async def confirm_action(sandbox_id: str):
    """
    用户点击"继续"按钮
    
    触发等待中的程序继续执行
    """
    if sandbox_id in user_confirmations:
        user_confirmations[sandbox_id]["confirmed"] = True
        user_confirmations[sandbox_id]["event"].set()
        return {"sandbox_id": sandbox_id, "status": "confirmed"}
    return {"sandbox_id": sandbox_id, "status": "no_wait"}


@app.get("/api/sandboxes/{sandbox_id}/wait-status")
async def get_wait_status(sandbox_id: str):
    """
    获取等待状态
    
    Returns:
        {
            "waiting": bool,  # 是否在等待用户确认
            "confirmed": bool  # 用户是否已确认
        }
    """
    if sandbox_id in user_confirmations:
        return {
            "waiting": True,
            "confirmed": user_confirmations[sandbox_id]["confirmed"]
        }
    return {"waiting": False, "confirmed": False}


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """
    健康检查

    Returns:
        {
            "status": "ok",
            "sessions": int,  # 会话数量
            "websockets": int  # WebSocket 连接数量
        }
    """
    return {
        "status": "ok",
        "sessions": len(chat_sessions),
        "websockets": sum(len(ws_list) for ws_list in chat_websockets.values()),
        "sandboxes": len(sandbox_urls),
    }


# ============ 服务器启动 ============


def start_server(host: str = "0.0.0.0", port: int = 8181):
    """
    启动服务器

    Args:
        host: 主机地址，默认 0.0.0.0（监听所有网络接口）
        port: 端口号，默认 8081
    """
    print(
        f"""
==============
AI Chat Server
http://localhost:{port}
==============

"""
    )

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
