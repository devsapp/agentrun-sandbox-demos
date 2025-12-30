"""
Runner 接口

提供 Sandbox 会话状态管理和 VNC 集成接口。
支持基于 user_id/session_id/thread_id 的多实例隔离。

使用方式：
    from runner import create_or_get_sandbox, set_vnc_url, destroy_sandbox
    
    # 创建或获取 Sandbox（支持会话隔离）
    sandbox_info = create_or_get_sandbox(
        user_id="user123",
        session_id="session456",
        thread_id="thread789"
    )
    
    # 设置 VNC URL（可选）
    set_vnc_url(
        sandbox_id=sandbox_info['sandbox_id'],
        vnc_url="ws://..."
    )
    
    # 销毁 Sandbox
    destroy_sandbox(sandbox_id=sandbox_info['sandbox_id'])
"""

import os
import sys
from typing import Optional, Dict, Any, Tuple
import threading
import atexit
import signal

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加当前目录（examples/）到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from sandbox_manager import SandboxManager


# ============ 全局状态管理 ============

# 保存所有 Sandbox 实例：key 是 (user_id, session_id, thread_id)，value 是 SandboxManager
_sandbox_instances: Dict[Tuple[str, str, str], SandboxManager] = {}

# 保存 Sandbox ID 到 session key 的映射，用于快速查找
_sandbox_id_to_key: Dict[str, Tuple[str, str, str]] = {}

# 线程锁，保证并发安全
_lock = threading.Lock()


# ============ Sandbox 管理 ============

def create_or_get_sandbox(
    user_id: str,
    session_id: str,
    thread_id: str,
    template_name: Optional[str] = None,
    idle_timeout: int = 600,
    force_recreate: bool = False
) -> Dict[str, Any]:
    """
    创建或获取 Sandbox（支持会话状态管理和隔离）
    
    Args:
        user_id: 用户 ID，用于用户级别隔离
        session_id: 会话 ID，用于会话级别隔离
        thread_id: 线程 ID，用于线程级别隔离
        template_name: 模板名称（可选）
        idle_timeout: 空闲超时时间（秒，默认 600）
        force_recreate: 是否强制重新创建（默认 False）
    
    Returns:
        dict: Sandbox 信息
            {
                "sandbox_id": str,
                "cdp_url": str,
                "vnc_url": str,
                "status": str,
                "is_new": bool  # 是否是新创建的
            }
    
    Raises:
        ValueError: 参数错误
        RuntimeError: 创建 Sandbox 失败
    
    使用示例：
        # 创建新 Sandbox
        sandbox_info = create_or_get_sandbox(
            user_id="user123",
            session_id="session456",
            thread_id="thread789"
        )
        
        # 再次调用返回同一个 Sandbox
        same_sandbox = create_or_get_sandbox(
            user_id="user123",
            session_id="session456",
            thread_id="thread789"
        )
        assert sandbox_info['sandbox_id'] == same_sandbox['sandbox_id']
    """
    # 参数验证
    if not user_id or not session_id or not thread_id:
        raise ValueError("user_id、session_id 和 thread_id 不能为空")
    
    session_key = (user_id, session_id, thread_id)
    
    with _lock:
        # 检查是否已存在
        if not force_recreate and session_key in _sandbox_instances:
            manager = _sandbox_instances[session_key]
            if manager.is_active():
                print(f"♻️  复用现有 Sandbox: {manager.get_sandbox_id()}")
                info = manager.get_info()
                if info:
                    info["is_new"] = False
                    return info
        
        # 创建新的 SandboxManager
        print(f"🔨 为会话创建新 Sandbox: user={user_id}, session={session_id}, thread={thread_id}")
        manager = SandboxManager()
        
        try:
            # 创建 Sandbox
            sandbox_info = manager.create(
                template_name=template_name,
                idle_timeout=idle_timeout
            )
            
            # 保存到全局字典
            _sandbox_instances[session_key] = manager
            _sandbox_id_to_key[sandbox_info["sandbox_id"]] = session_key
            
            # 标记为新创建
            sandbox_info["is_new"] = True
            
            return sandbox_info
            
        except Exception as e:
            # 创建失败，清理
            try:
                manager.destroy()
            except:
                pass
            raise RuntimeError(f"创建 Sandbox 失败: {e}")


def get_sandbox_info(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    sandbox_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    获取 Sandbox 信息
    
    可以通过 session key 或 sandbox_id 查询。
    
    Args:
        user_id: 用户 ID（与 session_id、thread_id 一起使用）
        session_id: 会话 ID
        thread_id: 线程 ID
        sandbox_id: Sandbox ID（可选，优先使用）
    
    Returns:
        dict or None: Sandbox 信息
    
    使用示例：
        # 通过 session key 查询
        info = get_sandbox_info(user_id="user123", session_id="session456", thread_id="thread789")
        
        # 通过 sandbox_id 查询
        info = get_sandbox_info(sandbox_id="sbx-xxxxx")
    """
    with _lock:
        # 优先使用 sandbox_id 查询
        if sandbox_id:
            session_key = _sandbox_id_to_key.get(sandbox_id)
            if session_key and session_key in _sandbox_instances:
                manager = _sandbox_instances[session_key]
                return manager.get_info()
            return None
        
        # 使用 session key 查询
        if user_id and session_id and thread_id:
            session_key = (user_id, session_id, thread_id)
            if session_key in _sandbox_instances:
                manager = _sandbox_instances[session_key]
                return manager.get_info()
        
        return None


def destroy_sandbox(sandbox_id: str) -> bool:
    """
    销毁指定的 Sandbox
    
    Args:
        sandbox_id: Sandbox ID
    
    Returns:
        bool: 是否成功销毁
    
    使用示例：
        destroy_sandbox(sandbox_id="sbx-xxxxx")
    """
    with _lock:
        # 查找 session key
        session_key = _sandbox_id_to_key.get(sandbox_id)
        if not session_key:
            print(f"⚠️  未找到 Sandbox: {sandbox_id}")
            return False
        
        # 获取 manager
        manager = _sandbox_instances.get(session_key)
        if not manager:
            print(f"⚠️  Sandbox 管理器不存在: {sandbox_id}")
            return False
        
        # 销毁
        try:
            manager.destroy()
            
            # 清理全局状态
            del _sandbox_instances[session_key]
            del _sandbox_id_to_key[sandbox_id]
            
            print(f"✅ Sandbox 已销毁: {sandbox_id}")
            return True
            
        except Exception as e:
            print(f"❌ 销毁 Sandbox 失败: {e}")
            return False


def destroy_all_sandboxes():
    """
    销毁所有 Sandbox
    
    使用示例：
        destroy_all_sandboxes()
    """
    with _lock:
        sandbox_ids = list(_sandbox_id_to_key.keys())
    
    for sandbox_id in sandbox_ids:
        destroy_sandbox(sandbox_id)


# ============ 自动清理机制 ============

def _cleanup_on_exit():
    """程序退出时自动清理所有 sandbox"""
    with _lock:
        if not _sandbox_instances:
            return
        
        print("\n🧹 程序退出,正在清理所有 Sandbox...")
    
    try:
        destroy_all_sandboxes()
        print("✅ Sandbox 清理完成")
    except Exception as e:
        print(f"⚠️  清理 Sandbox 时出错: {e}")


def _signal_handler(signum, frame):
    """处理系统信号(SIGINT, SIGTERM)"""
    signal_names = {
        signal.SIGINT: "SIGINT (Ctrl+C)",
        signal.SIGTERM: "SIGTERM (kill)"
    }
    signal_name = signal_names.get(signum, f"Signal {signum}")
    
    print(f"\n⚠️  收到信号: {signal_name}")
    _cleanup_on_exit()
    sys.exit(0)


# 注册程序退出时的清理函数
atexit.register(_cleanup_on_exit)

# 注册信号处理器
try:
    signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, _signal_handler)  # kill 命令
except (ValueError, OSError):
    # Windows 或某些环境可能不支持某些信号
    pass


# ============ VNC 集成 ============

def set_cdp_url(sandbox_id: str, cdp_url: str, vnc_server_url: Optional[str] = None) -> bool:
    """
    设置 CDP URL 到 VNC Server
    
    Args:
        sandbox_id: Sandbox ID
        cdp_url: CDP WebSocket URL
        vnc_server_url: VNC Server URL（可选，默认从环境变量读取）
    
    Returns:
        bool: 是否成功设置
    
    使用示例：
        set_cdp_url(
            sandbox_id="sbx-xxxxx",
            cdp_url="ws://example.com/cdp"
        )
    """
    if not vnc_server_url:
        vnc_server_url = os.getenv("VNC_SERVER_URL", "http://localhost:8080")
    
    try:
        import httpx
        
        # 设置 CDP URL（VNC Server 会自动创建记录）
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{vnc_server_url}/api/sandboxes/{sandbox_id}/cdp",
                json={"cdp_url": cdp_url}
            )
            
            if response.status_code == 200:
                print(f"✅ CDP URL 已设置: {sandbox_id}")
                return True
            else:
                print(f"⚠️  设置 CDP URL 失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"⚠️  设置 CDP URL 异常: {e}")
        return False


def set_vnc_url(sandbox_id: str, vnc_url: str, vnc_server_url: Optional[str] = None) -> bool:
    """
    设置 VNC URL 到 VNC Server
    
    可以被 browseruse example 调用，用于更新 VNC viewer 的连接。
    
    Args:
        sandbox_id: Sandbox ID
        vnc_url: VNC WebSocket URL
        vnc_server_url: VNC Server URL（可选，默认从环境变量读取）
    
    Returns:
        bool: 是否成功设置
    
    使用示例:
        set_vnc_url(
            sandbox_id="sbx-xxxxx",
            vnc_url="ws://example.com/vnc"
        )
    """
    if not vnc_server_url:
        vnc_server_url = os.getenv("VNC_SERVER_URL", "http://localhost:8080")
    
    try:
        import httpx
        
        # 直接设置 VNC URL（VNC Server 会自动创建记录）
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{vnc_server_url}/api/sandboxes/{sandbox_id}/vnc",
                json={"vnc_url": vnc_url}
            )
            
            if response.status_code == 200:
                print(f"✅ VNC URL 已设置: {sandbox_id}")
                return True
            else:
                print(f"⚠️  设置 VNC URL 失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"⚠️  设置 VNC URL 异常: {e}")
        return False


def set_sandbox_urls(
    sandbox_id: str,
    cdp_url: Optional[str] = None,
    vnc_url: Optional[str] = None,
    vnc_server_url: Optional[str] = None
) -> bool:
    """
    同时设置 CDP URL 和 VNC URL 到 VNC Server（便捷方法）
    
    Args:
        sandbox_id: Sandbox ID
        cdp_url: CDP WebSocket URL（可选）
        vnc_url: VNC WebSocket URL（可选）
        vnc_server_url: VNC Server URL（可选，默认从环境变量读取）
    
    Returns:
        bool: 是否全部成功设置
    
    使用示例：
        set_sandbox_urls(
            sandbox_id="sbx-xxxxx",
            cdp_url="ws://example.com/cdp",
            vnc_url="ws://example.com/vnc"
        )
    """
    success = True
    
    if cdp_url:
        if not set_cdp_url(sandbox_id, cdp_url, vnc_server_url):
            success = False
    
    if vnc_url:
        if not set_vnc_url(sandbox_id, vnc_url, vnc_server_url):
            success = False
    
    return success


def get_vnc_viewer_url(sandbox_id: str, vnc_server_url: Optional[str] = None) -> Optional[str]:
    """
    获取 VNC Viewer URL
    
    Args:
        sandbox_id: Sandbox ID
        vnc_server_url: VNC Server URL（可选，默认从环境变量读取）
    
    Returns:
        str or None: VNC Viewer URL
    
    使用示例：
        viewer_url = get_vnc_viewer_url(sandbox_id="sbx-xxxxx")
        print(f"打开浏览器访问: {viewer_url}")
    """
    if not vnc_server_url:
        vnc_server_url = os.getenv("VNC_SERVER_URL", "http://localhost:8080")
    
    # 使用 sandbox_id 作为 session_id
    return f"{vnc_server_url}/viewer/{sandbox_id}"


# ============ 导出接口 ============

__all__ = [
    'create_or_get_sandbox',    # 创建或获取 Sandbox
    'get_sandbox_info',         # 获取 Sandbox 信息
    'destroy_sandbox',          # 销毁指定 Sandbox
    'destroy_all_sandboxes',    # 销毁所有 Sandbox
    'set_vnc_url',              # 设置 VNC URL
    'get_vnc_viewer_url',       # 获取 VNC Viewer URL
]


# ============ 测试代码 ============

if __name__ == "__main__":
    # 测试代码
    print("="*60)
    print("Runner 接口测试")
    print("="*60)
    
    try:
        # 测试 1: 创建 Sandbox
        print("\n1. 测试创建 Sandbox:")
        sandbox1 = create_or_get_sandbox(
            user_id="test_user",
            session_id="test_session",
            thread_id="test_thread"
        )
        print(f"✅ Sandbox 创建成功")
        print(f"   Sandbox ID: {sandbox1['sandbox_id']}")
        print(f"   CDP URL: {sandbox1['cdp_url'][:60]}...")
        print(f"   Is New: {sandbox1['is_new']}")
        
        # 测试 2: 复用 Sandbox
        print("\n2. 测试复用 Sandbox:")
        sandbox2 = create_or_get_sandbox(
            user_id="test_user",
            session_id="test_session",
            thread_id="test_thread"
        )
        print(f"✅ 复用成功")
        print(f"   Same ID: {sandbox1['sandbox_id'] == sandbox2['sandbox_id']}")
        print(f"   Is New: {sandbox2['is_new']}")
        
        # 测试 3: 获取信息
        print("\n3. 测试获取 Sandbox 信息:")
        info = get_sandbox_info(sandbox_id=sandbox1['sandbox_id'])
        print(f"✅ 信息获取成功: {info is not None}")
        
        # 测试 4: 设置 VNC URL（如果 VNC Server 运行）
        print("\n4. 测试设置 VNC URL:")
        if sandbox1.get('vnc_url'):
            set_vnc_url(
                sandbox_id=sandbox1['sandbox_id'],
                vnc_url=sandbox1['vnc_url']
            )
            viewer_url = get_vnc_viewer_url(sandbox1['sandbox_id'])
            print(f"   Viewer URL: {viewer_url}")
        
        # 测试 5: 销毁 Sandbox
        print("\n5. 测试销毁 Sandbox:")
        success = destroy_sandbox(sandbox1['sandbox_id'])
        print(f"✅ 销毁{'成功' if success else '失败'}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理所有 Sandbox
        print("\n清理所有 Sandbox...")
        destroy_all_sandboxes()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
