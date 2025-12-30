"""
Sandbox 生命周期管理模块

负责 AgentRun Browser Sandbox 的创建、管理和销毁。
提供统一的接口供 LangChain Agent 使用。
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class SandboxManager:
    """Sandbox 生命周期管理器"""
    
    def __init__(self):
        self._sandbox: Optional[Any] = None
        self._sandbox_id: Optional[str] = None
        self._cdp_url: Optional[str] = None
        self._vnc_url: Optional[str] = None
    
    def create(
        self,
        template_name: Optional[str] = None,
        idle_timeout: int = 3000
    ) -> Dict[str, Any]:
        """
        创建或获取一个浏览器 sandbox 实例
        
        Args:
            template_name: Sandbox 模板名称，如果为 None 则从环境变量读取
            idle_timeout: 空闲超时时间（秒），默认 3000 秒
        
        Returns:
            dict: 包含 sandbox_id, cdp_url, vnc_url 的字典
        
        Raises:
            RuntimeError: 创建失败时抛出异常
        """
        try:
            from agentrun.sandbox import Sandbox, TemplateType
            
            # 如果已有 sandbox，直接返回
            if self._sandbox is not None:
                return self.get_info()
            
            # 从环境变量获取模板名称
            if template_name is None:
                template_name = os.getenv(
                    "BROWSER_TEMPLATE_NAME",
                    "sandbox-browser-demo"
                )
            
            # 创建 sandbox
            self._sandbox = Sandbox.create(
                template_type=TemplateType.BROWSER,
                template_name=template_name,
                sandbox_idle_timeout_seconds=idle_timeout
            )
            
            self._sandbox_id = self._sandbox.sandbox_id
            self._cdp_url = self._get_cdp_url()
            self._vnc_url = self._get_vnc_url()
            
            return self.get_info()
        
        except ImportError as e:
            print(e)
            raise RuntimeError(
                "agentrun-sdk 未安装，请运行: pip install agentrun-sdk[playwright,server]"
            )
        except Exception as e:
            raise RuntimeError(f"创建 Sandbox 失败: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取当前 sandbox 的信息
        
        Returns:
            dict: 包含 sandbox_id, cdp_url, vnc_url 的字典
        
        Raises:
            RuntimeError: 如果没有活动的 sandbox
        """
        if self._sandbox is None:
            raise RuntimeError("没有活动的 sandbox，请先创建")
        
        return {
            "sandbox_id": self._sandbox_id,
            "cdp_url": self._cdp_url,
            "vnc_url": self._vnc_url,
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
    
    def _get_cdp_url(self) -> str:
        """从 sandbox 对象获取 CDP URL"""
        if self._sandbox is None:
            return ""
        
        # 尝试从 sandbox 对象获取 CDP URL
        if hasattr(self._sandbox, 'cdp_url'):
            return self._sandbox.cdp_url
        
        if hasattr(self._sandbox, 'cdp_endpoint'):
            return self._sandbox.cdp_endpoint
        
        # 根据 sandbox_id 构造 CDP URL
        try:
            account_id = os.getenv("AGENTRUN_ACCOUNT_ID") or os.getenv("ALIBABA_CLOUD_ACCOUNT_ID")
            region = os.getenv("ALIBABA_CLOUD_REGION", "cn-hangzhou")
            
            if account_id:
                return f"wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{self._sandbox_id}/ws/automation"
        except:
            pass
        
        raise RuntimeError("无法获取 CDP URL")
    
    def _get_vnc_url(self) -> Optional[str]:
        """从 sandbox 对象获取 VNC URL"""
        if self._sandbox is None:
            return None
        
        # 尝试从 sandbox 对象获取 VNC URL
        vnc_url = None
        if hasattr(self._sandbox, 'vnc_url'):
            vnc_url = self._sandbox.vnc_url
        elif hasattr(self._sandbox, 'vnc_endpoint'):
            vnc_url = self._sandbox.vnc_endpoint
        
        # 修复 VNC URL 路径
        if vnc_url and vnc_url.endswith('/vnc'):
            vnc_url = vnc_url[:-4] + '/ws/livestream'
        
        # 如果还是没有，根据 sandbox_id 构造
        if not vnc_url:
            try:
                account_id = os.getenv("AGENTRUN_ACCOUNT_ID") or os.getenv("ALIBABA_CLOUD_ACCOUNT_ID")
                region = os.getenv("ALIBABA_CLOUD_REGION", "cn-hangzhou")
                
                if account_id:
                    vnc_url = f"wss://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{self._sandbox_id}/ws/livestream"
            except:
                pass
        
        return vnc_url
    
    def destroy(self) -> str:
        """
        销毁当前的 sandbox 实例
        
        Returns:
            str: 操作结果描述
        """
        if self._sandbox is None:
            return "⚠️ 没有活动的 sandbox"
        
        try:
            sandbox_id = self._sandbox_id
            
            # 尝试销毁 sandbox
            if hasattr(self._sandbox, 'delete'):
                self._sandbox.delete()
            elif hasattr(self._sandbox, 'stop'):
                self._sandbox.stop()
            elif hasattr(self._sandbox, 'destroy'):
                self._sandbox.destroy()
            
            # 清理状态
            self._sandbox = None
            self._sandbox_id = None
            self._cdp_url = None
            self._vnc_url = None
            
            return f"✅ Sandbox 已销毁: {sandbox_id}"
        
        except Exception as e:
            # 即使销毁失败，也清理本地状态
            self._sandbox = None
            self._sandbox_id = None
            self._cdp_url = None
            self._vnc_url = None
            return f"⚠️ 销毁 Sandbox 时出错: {str(e)}"
    
    def is_active(self) -> bool:
        """检查 sandbox 是否活跃"""
        return self._sandbox is not None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，自动销毁"""
        self.destroy()
        return False


# 全局单例（可选，用于简单场景）
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
    if _global_manager:
        _global_manager.destroy()
    _global_manager = None


# ============ 测试函数 ============

def test_sandbox_operations():
    """测试 Sandbox 的创建、获取信息、使用和销毁"""
    print("=" * 60)
    print("Sandbox 生命周期测试")
    print("=" * 60)
    print()
    
    manager = SandboxManager()
    
    try:
        # 测试 1: 创建 Sandbox
        print("📝 测试 1: 创建 Sandbox")
        print("-" * 60)
        try:
            info = manager.create()
            print(f"✅ Sandbox 创建成功！")
            print(f"   - Sandbox ID: {info['sandbox_id']}")
            print(f"   - CDP URL: {info['cdp_url'][:80]}...")
            if info.get('vnc_url'):
                print(f"   - VNC URL: {info['vnc_url'][:80]}...")
            print()
        except Exception as e:
            print(f"❌ 创建失败: {str(e)}")
            print()
            return
        
        # 测试 2: 获取信息
        print("📝 测试 2: 获取 Sandbox 信息")
        print("-" * 60)
        try:
            info = manager.get_info()
            print(f"✅ 获取信息成功！")
            print(f"   - Sandbox ID: {info['sandbox_id']}")
            print(f"   - CDP URL: {info['cdp_url']}")
            if info.get('vnc_url'):
                print(f"   - VNC URL: {info['vnc_url']}")
                print(f"\n💡 提示: 您可以使用 VNC URL 在 vnc.html 中测试连接")
            print()
        except Exception as e:
            print(f"❌ 获取信息失败: {str(e)}")
            print()
        
        # 测试 3: 使用 Sandbox（通过 CDP 连接浏览器）
        print("📝 测试 3: 使用 Sandbox（连接浏览器）")
        print("-" * 60)
        try:
            cdp_url = manager.get_cdp_url()
            if cdp_url:
                print(f"✅ CDP URL 可用: {cdp_url[:80]}...")
                
                # 尝试使用 Playwright 连接
                try:
                    from playwright.sync_api import sync_playwright
                    
                    print("   正在尝试连接浏览器...")
                    with sync_playwright() as p:
                        browser = p.chromium.connect_over_cdp(cdp_url)
                        pages = browser.contexts[0].pages if browser.contexts else []
                        
                        if pages:
                            page = pages[0]
                            print(f"   ✅ 已连接到浏览器")
                            print(f"   - 当前页面数: {len(pages)}")
                            print(f"   - 第一个页面标题: {page.title()}")
                            
                            # 尝试导航到一个测试页面
                            print("\n   正在导航到测试页面...")
                            page.goto("https://www.aliyun.com", timeout=30000)
                            title = page.title()
                            print(f"   ✅ 导航成功！")
                            print(f"   - 页面标题: {title}")
                        else:
                            print("   ⚠️ 没有打开的页面，创建新页面...")
                            page = browser.new_page()
                            page.goto("https://www.aliyun.com", timeout=30000)
                            print(f"   ✅ 新页面创建并导航成功！")
                            print(f"   - 页面标题: {page.title()}")
                
                except ImportError:
                    print("   ⚠️ Playwright 未安装，跳过浏览器连接测试")
                    print("   💡 提示: 安装 playwright 以启用浏览器操作 (pip install playwright)")
                except Exception as e:
                    print(f"   ⚠️ 浏览器连接失败: {str(e)}")
                    print("   💡 提示: 这可能是正常的，如果 Sandbox 还未完全启动")
            else:
                print("   ❌ CDP URL 不可用")
            print()
        except Exception as e:
            print(f"❌ 使用 Sandbox 失败: {str(e)}")
            print()
        
        # 测试 4: 检查状态
        print("📝 测试 4: 检查 Sandbox 状态")
        print("-" * 60)
        is_active = manager.is_active()
        print(f"✅ Sandbox 状态: {'活跃' if is_active else '非活跃'}")
        if is_active:
            info = manager.get_info()
            print(f"   - Sandbox ID: {info['sandbox_id']}")
        print()
        
        # 测试 5: 销毁 Sandbox
        print("📝 测试 5: 销毁 Sandbox")
        print("-" * 60)
        result = manager.destroy()
        print(result)
        print()
        
        # 验证销毁
        is_active_after = manager.is_active()
        print(f"✅ 销毁后状态检查: {'仍活跃' if is_active_after else '已销毁'}")
        print()
        
        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 确保清理资源
        try:
            manager.destroy()
        except:
            pass


if __name__ == "__main__":
    test_sandbox_operations()

