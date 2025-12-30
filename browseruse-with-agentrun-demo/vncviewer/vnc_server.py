"""
VNC Manager Server - 简化版（职责明确）

VNC Server 的唯一职责：
1. 接收日志并推送到前端
2. 接收和提供 CDP/VNC URL
3. 托管前端页面

不负责：
- ❌ Sandbox 的创建和管理（由 runner.py 负责）
- ❌ Session 的主动创建（自动创建即可）
- ❌ Session 的生命周期管理（由 runner.py 负责）
"""

import asyncio
import os
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============ FastAPI 应用 ============

app = FastAPI(
    title="VNC Manager Server",
    description="轻量级 VNC 展示和中转服务",
    version="2.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ============ 数据模型 ============

class LogEntry(BaseModel):
    """日志条目"""
    level: str
    message: str
    extra: Optional[Dict] = None


class URLInfo(BaseModel):
    """URL 信息"""
    cdp_url: Optional[str] = None
    vnc_url: Optional[str] = None


# ============ 全局状态 ============

# Sandbox URL 存储
# {sandbox_id: {"cdp_url": str, "vnc_url": str, "last_access_at": float}}
sandbox_urls: Dict[str, Dict] = {}

# 日志队列（每个 Sandbox 最多保留 1000 条日志）
# {sandbox_id: deque([log_entry, ...])}
log_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

# WebSocket 连接池
# {sandbox_id: [websocket, ...]}
log_websockets: Dict[str, List[WebSocket]] = defaultdict(list)

# ============ 前端页面 ============

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """根目录，显示所有活跃的 Sandbox"""
    html_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>VNC Manager Server</h1><p>前端文件未找到</p>")


@app.get("/viewer/{sandbox_id}", response_class=HTMLResponse)
async def view_sandbox(sandbox_id: str):
    """查看器页面"""
    html_path = os.path.join(FRONTEND_DIR, "viewer.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content=f"<h1>Sandbox: {sandbox_id}</h1><p>前端文件未找到</p>")


# ============ Sandbox 信息 API ============

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
                "last_access_at": float,
                "log_count": int
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
            "log_count": len(log_queues.get(sandbox_id, [])),
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
            "last_access_at": float,
            "log_count": int
        }
    """
    if sandbox_id not in sandbox_urls:
        # 不抛出 404，返回空信息（允许查询未设置 URL 的 Sandbox）
        return {
            "sandbox_id": sandbox_id,
            "cdp_url": None,
            "vnc_url": None,
            "last_access_at": None,
            "log_count": len(log_queues.get(sandbox_id, [])),
        }
    
    data = sandbox_urls[sandbox_id]
    data["last_access_at"] = time.time()
    
    return {
        "sandbox_id": sandbox_id,
        "cdp_url": data.get("cdp_url"),
        "vnc_url": data.get("vnc_url"),
        "last_access_at": data.get("last_access_at"),
        "log_count": len(log_queues.get(sandbox_id, [])),
    }


# ============ URL 设置 API ============

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


# ============ 日志 API ============

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
    # 添加时间戳
    log_data = {
        "level": log_entry.level,
        "message": log_entry.message,
        "extra": log_entry.extra,
        "timestamp": time.time(),
    }
    
    # 保存到日志队列
    log_queues[sandbox_id].append(log_data)
    
    # 推送到 WebSocket 客户端
    # ✅ 修复：发送完整的日志数据（level, message, timestamp, extra）
    if sandbox_id in log_websockets:
        for ws in list(log_websockets[sandbox_id]):
            try:
                await ws.send_json({
                    "type": "log",
                    "level": log_data["level"],
                    "message": log_data["message"],
                    "timestamp": log_data["timestamp"],
                    "extra": log_data["extra"]
                })
            except:
                # WebSocket 已关闭，移除
                log_websockets[sandbox_id].remove(ws)
    
    return {"sandbox_id": sandbox_id}


@app.get("/api/log/{sandbox_id}")
async def get_logs(sandbox_id: str, limit: int = 100):
    """
    获取历史日志
    
    Query:
        limit: 最多返回多少条日志（默认 100）
    
    Returns:
        {
            "sandbox_id": str,
            "logs": [
                {
                    "level": str,
                    "message": str,
                    "extra": dict,
                    "timestamp": float
                },
                ...
            ]
        }
    """
    logs = list(log_queues.get(sandbox_id, []))
    
    # 只返回最后 limit 条
    if len(logs) > limit:
        logs = logs[-limit:]
    
    return {
        "sandbox_id": sandbox_id,
        "logs": logs,
    }


@app.websocket("/ws/log/{sandbox_id}")
async def websocket_log_endpoint(websocket: WebSocket, sandbox_id: str):
    """WebSocket 日志流端点"""
    await websocket.accept()
    log_websockets[sandbox_id].append(websocket)
    
    print(f"WebSocket connected for sandbox {sandbox_id}. Total: {len(log_websockets[sandbox_id])}")
    
    try:
        # 发送历史日志
        # ✅ 修复：发送完整的日志数据（level, message, timestamp, extra）
        history_logs = list(log_queues.get(sandbox_id, []))
        for log_data in history_logs:
            await websocket.send_json({
                "type": "log",
                "level": log_data["level"],
                "message": log_data["message"],
                "timestamp": log_data["timestamp"],
                "extra": log_data["extra"]
            })
        
        # 保持连接
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_websockets[sandbox_id].remove(websocket)
        print(f"WebSocket disconnected for sandbox {sandbox_id}. Remaining: {len(log_websockets[sandbox_id])}")
    except Exception as e:
        print(f"WebSocket error for sandbox {sandbox_id}: {e}")
        if websocket in log_websockets[sandbox_id]:
            log_websockets[sandbox_id].remove(websocket)


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "sandboxes": len(sandbox_urls),
        "active_logs": len(log_queues),
        "websockets": sum(len(ws_list) for ws_list in log_websockets.values()),
    }


# ============ 服务器启动 ============

def start_server(host: str = "0.0.0.0", port: int = 8080):
    """
    启动服务器
    
    Args:
        host: 主机地址
        port: 端口号
    """
    print(f"""
==============
http://localhost:{port}
==============

""")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

