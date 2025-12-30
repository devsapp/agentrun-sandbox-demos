"""
Sandbox Manager - 使用 agentrun SDK

负责 Sandbox 的创建、管理和销毁。
基于 agentrun SDK，提供简单的接口供 runner.py 使用。

内部实现细节：
- 使用 agentrun.sandbox.Sandbox 创建浏览器沙箱
- 自动获取 CDP URL 和 VNC URL
- 管理 Sandbox 生命周期
"""

import os
import sys
from typing import Optional, Dict, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class SandboxManager:
    """Sandbox 管理器 - 使用 agentrun SDK"""
    
    def __init__(self):
        self._sandbox = None
        self._sandbox_id = None
        self._cdp_url = None
        self._vnc_url = None
    
    def create(self, template_name: Optional[str] = None, idle_timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        创建 Sandbox
        
        Args:
            template_name: 模板名称（可选）
            idle_timeout: 空闲超时时间（秒）。如果未指定，则从配置文件读取
        
        Returns:
            dict: Sandbox 信息
                {
                    "sandbox_id": str,
                    "cdp_url": str,
                    "vnc_url": str,
                    "status": str
                }
        
        Raises:
            RuntimeError: 创建失败
        """
        try:
            from agentrun.sandbox import Sandbox, TemplateType
            from config import get_settings
            
            # 如果未指定 idle_timeout，从配置读取
            if idle_timeout is None:
                settings = get_settings()
                idle_timeout = settings.sandbox_idle_timeout
            
            print(f"🔨 正在创建 Sandbox（空闲超时: {idle_timeout} 秒）...")
            
            # 创建浏览器沙箱
            self._sandbox = Sandbox.create(
                template_type=TemplateType.BROWSER,
                template_name=template_name or "browser-sandbox",
                sandbox_idle_timeout_seconds=idle_timeout
            )
            
            self._sandbox_id = self._sandbox.sandbox_id
            
            # 获取 CDP URL 和 VNC URL
            self._cdp_url = self._get_cdp_url_from_sandbox()
            self._vnc_url = self._get_vnc_url_from_sandbox()
            
            print(f"✅ Sandbox 创建成功")
            print(f"   Sandbox ID: {self._sandbox_id}")
            print(f"   CDP URL: {self._cdp_url[:60]}...")
            if self._vnc_url:
                print(f"   VNC URL: {self._vnc_url[:60]}...")
            
            return {
                "sandbox_id": self._sandbox_id,
                "cdp_url": self._cdp_url,
                "vnc_url": self._vnc_url,
                "status": getattr(self._sandbox, 'status', 'RUNNING')
            }
            
        except ImportError:
            raise RuntimeError(
                "agentrun SDK 未安装。请运行：\n"
                "  pip install agentrun-sdk[playwright]"
            )
        except Exception as e:
            raise RuntimeError(f"创建 Sandbox 失败: {e}")
    
    def _get_cdp_url_from_sandbox(self) -> str:
        """从 sandbox 对象获取 CDP URL"""
        # 尝试从 sandbox 对象获取 CDP URL
        if hasattr(self._sandbox, 'cdp_url'):
            return self._sandbox.cdp_url
        
        if hasattr(self._sandbox, 'cdp_endpoint'):
            return self._sandbox.cdp_endpoint
        
        # 如果没有直接属性，根据 sandbox_id 和配置构造
        try:
            from config import get_settings
            settings = get_settings()
            region = settings.alibaba_cloud_region or os.getenv("AGENTRUN_REGION", "cn-hangzhou")
            account_id = settings.alibaba_cloud_account_id or os.getenv("AGENTRUN_ACCOUNT_ID")
            
            if account_id:
                # 格式：wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{sandbox_id}/ws/automation
                # return f"wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{self._sandbox_id}/ws/automation"
                return f"wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{self._sandbox_id}/ws/automation"
        except:
            pass
        
        # 默认格式
        raise RuntimeError("Failed to get CDP URL from sandbox")
    
    def _get_vnc_url_from_sandbox(self) -> Optional[str]:
        """从 sandbox 对象获取 VNC URL"""
        # 尝试从 sandbox 对象获取 VNC URL
        if hasattr(self._sandbox, 'vnc_url'):
            vnc_url = self._sandbox.vnc_url
            # ✅ 修复：将错误的 /vnc 路径替换为正确的 /ws/livestream
            if vnc_url and vnc_url.endswith('/vnc'):
                vnc_url = vnc_url[:-4] + '/ws/livestream'
            return vnc_url
        
        if hasattr(self._sandbox, 'vnc_endpoint'):
            vnc_url = self._sandbox.vnc_endpoint
            # ✅ 修复：将错误的 /vnc 路径替换为正确的 /ws/livestream
            if vnc_url and vnc_url.endswith('/vnc'):
                vnc_url = vnc_url[:-4] + '/ws/livestream'
            return vnc_url
        
        # 如果没有直接属性，根据 sandbox_id 和配置构造
        try:
            from config import get_settings
            settings = get_settings()
            region = settings.alibaba_cloud_region or os.getenv("AGENTRUN_REGION", "cn-hangzhou")
            account_id = settings.alibaba_cloud_account_id or os.getenv("AGENTRUN_ACCOUNT_ID")
            
            if account_id:
                # ✅ 修复：使用正确的 VNC URL 路径 /ws/livestream
                # 格式：wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{sandbox_id}/ws/livestream
                # return f"wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{self._sandbox_id}/ws/livestream"
                return f"wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{self._sandbox_id}/ws/livestream"
        except:
            pass
        
        raise RuntimeError("Failed to get VNC URL from sandbox")

    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """
        获取 Sandbox 信息
        
        Returns:
            dict or None: Sandbox 信息
        """
        if self._sandbox_id is None:
            return None
        
        return {
            "sandbox_id": self._sandbox_id,
            "cdp_url": self._cdp_url,
            "vnc_url": self._vnc_url,
            "status": getattr(self._sandbox, 'status', 'UNKNOWN') if self._sandbox else 'UNKNOWN'
        }
    
    def get_cdp_url(self) -> Optional[str]:
        """获取 CDP URL"""
        return self._cdp_url
    
    def get_vnc_url(self) -> Optional[str]:
        """获取 VNC URL"""
        return self._vnc_url
    
    def get_sandbox_id(self) -> Optional[str]:
        """获取 Sandbox ID"""
        return self._sandbox_id
    
    def destroy(self):
        """销毁 Sandbox"""
        if self._sandbox is None:
            return
        
        sandbox_id = self._sandbox_id
        
        try:
            print(f"🗑️  正在销毁 Sandbox: {sandbox_id}")
            
            # 尝试调用 SDK 的删除方法
            method_used = None
            if hasattr(self._sandbox, 'delete'):
                self._sandbox.delete()
                method_used = 'delete()'
            elif hasattr(self._sandbox, 'stop'):
                self._sandbox.stop()
                method_used = 'stop()'
            elif hasattr(self._sandbox, 'destroy'):
                self._sandbox.destroy()
                method_used = 'destroy()'
            else:
                print(f"⚠️  Sandbox 对象没有可用的清理方法")
                method_used = None
            
            if method_used:
                print(f"✅ Sandbox 已销毁 (使用 {method_used})")
            
        except Exception as e:
            print(f"⚠️  销毁 Sandbox 时出错: {e}")
            # 如果需要调试,可以打印详细错误
            # import traceback
            # traceback.print_exc()
        finally:
            # 无论成功与否,都清理本地状态
            self._sandbox = None
            self._sandbox_id = None
            self._cdp_url = None
            self._vnc_url = None
    
    def is_active(self) -> bool:
        """检查 Sandbox 是否活跃"""
        return self._sandbox is not None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.destroy()
        return False


# 全局单例
_global_manager: Optional[SandboxManager] = None


def get_global_manager() -> SandboxManager:
    """获取全局 SandboxManager 单例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = SandboxManager()
    return _global_manager


def reset_global_manager():
    """重置全局 SandboxManager"""
    global _global_manager
    if _global_manager and _global_manager.is_active():
        _global_manager.destroy()
    _global_manager = None


if __name__ == "__main__":
    # 测试代码
    print("="*60)
    print("SandboxManager 测试（使用 agentrun SDK）")
    print("="*60)
    
    try:
        # 创建 SandboxManager
        manager = SandboxManager()
        
        # 创建 Sandbox（使用配置文件中的默认超时时间）
        print("\n1. 测试创建 Sandbox:")
        sandbox_info = manager.create()
        print(f"✅ Sandbox 信息: {sandbox_info}")
        
        # 获取信息
        print("\n2. 测试获取信息:")
        info = manager.get_info()
        print(f"✅ CDP URL: {info['cdp_url'][:60]}...")
        print(f"✅ VNC URL: {info['vnc_url'][:60] if info['vnc_url'] else 'N/A'}...")
        
        # 销毁 Sandbox
        print("\n3. 测试销毁 Sandbox:")
        manager.destroy()
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
