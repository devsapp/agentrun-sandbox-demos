"""
Examples Common Module - 示例代码通用模块

这个模块为所有示例提供统一的抽象接口，避免示例代码直接依赖平台特殊差异的底层实现。

主要功能：
1. 提供统一的 Logger 接口
2. 抽象 VNC 相关功能
3. 提供示例代码常用的工具函数

设计原则：
- 示例代码应该专注于业务逻辑，而不是底层实现细节
- 所有平台特殊差异应该在这个模块中统一处理
- 提供简洁、易用的 API
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class ExampleLogger:
    """
    示例代码专用的 Logger
    
    提供基础的日志接口，封装 VNCLogger。
    如果 VNC Server 不可用，则优雅降级（静默失败）。
    
    使用方法：
        logger = create_logger(session_id="xxx")
        logger.info("ℹ️ 信息")
        logger.debug("🔍 调试信息")
        logger.warning("⚠️ 警告")
        logger.error("❌ 错误")
    """
    
    def __init__(self, session_id: str, server_url: str = "http://localhost:8080"):
        """
        初始化 Logger
        
        Args:
            session_id: 会话 ID
            server_url: VNC Server 地址（默认: http://localhost:8080）
        """
        self.session_id = session_id
        self.server_url = server_url
        self._vnc_logger = None
        self._vnc_available = False
        
        # 尝试初始化 VNC Logger
        self._init_vnc_logger()
    
    def _init_vnc_logger(self):
        """初始化 VNC Logger（如果可用）"""
        try:
            from vncviewer import VNCLogger
            self._vnc_logger = VNCLogger(
                session_id=self.session_id,
                server_url=self.server_url
            )
            self._vnc_available = True
        except Exception:
            # VNC Logger 不可用，静默失败
            self._vnc_available = False
    
    def _log(self, level: str, message: str):
        """
        内部日志方法
        
        Args:
            level: 日志级别（INFO, DEBUG, WARNING, ERROR）
            message: 日志消息
        """
        if self._vnc_available and self._vnc_logger:
            try:
                # 调用 VNCLogger 的对应方法
                method = getattr(self._vnc_logger, level.lower(), None)
                if method:
                    method(message)
            except Exception:
                # 如果发送失败，静默忽略
                pass
    
    def info(self, message: str):
        """记录信息日志"""
        self._log("INFO", message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self._log("DEBUG", message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self._log("WARNING", message)
    
    def error(self, message: str):
        """记录错误日志"""
        self._log("ERROR", message)
    
    def close(self):
        """关闭 Logger"""
        if self._vnc_logger:
            try:
                self._vnc_logger.close()
            except Exception:
                pass
    
    def is_vnc_available(self) -> bool:
        """检查 VNC Logger 是否可用"""
        return self._vnc_available
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class VNCLoggingHandler(logging.Handler):
    """
    Python logging Handler - 将所有 Python logging 输出转发到 VNC Server
    
    这个 Handler 可以捕获所有使用 Python logging 模块的日志输出，
    包括第三方库（如 BrowserUse）的日志。
    """
    
    def __init__(self, vnc_logger: ExampleLogger):
        """
        初始化 Handler
        
        Args:
            vnc_logger: ExampleLogger 实例
        """
        super().__init__()
        self.vnc_logger = vnc_logger
    
    def emit(self, record: logging.LogRecord):
        """
        处理日志记录
        
        Args:
            record: logging.LogRecord 对象
        """
        try:
            # 格式化日志消息
            msg = self.format(record)
            
            # 根据日志级别转发到 VNC Logger
            level_name = record.levelname
            if level_name == "DEBUG":
                self.vnc_logger.debug(msg)
            elif level_name == "INFO":
                self.vnc_logger.info(msg)
            elif level_name == "WARNING":
                self.vnc_logger.warning(msg)
            elif level_name == "ERROR" or level_name == "CRITICAL":
                self.vnc_logger.error(msg)
            else:
                self.vnc_logger.info(msg)
        except Exception as e:
            # 调试：打印异常信息
            import sys
            import traceback
            print(f"[VNCLoggingHandler] Error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def create_logger(
    session_id: str,
    server_url: str = "http://localhost:8080",
    capture_python_logging: bool = True
) -> ExampleLogger:
    """
    创建 Logger（工厂函数）
    
    Args:
        session_id: 会话 ID
        server_url: VNC Server 地址
        capture_python_logging: 是否捕获 Python logging 输出（默认: True）
                                启用后，所有使用 logging 模块的日志都会转发到 VNC
    
    Returns:
        ExampleLogger 实例
    
    示例：
        # 基础用法
        logger = create_logger("my_session")
        logger.info("Hello World")
        
        # 启用 Python logging 拦截（默认已启用）
        logger = create_logger("my_session", capture_python_logging=True)
        # 现在所有 logging.info(), logging.warning() 等都会转发到 VNC
    """
    vnc_logger = ExampleLogger(session_id=session_id, server_url=server_url)
    
    # 如果启用了 Python logging 拦截，添加 Handler
    if capture_python_logging and vnc_logger.is_vnc_available():
        try:
            # 创建 Handler
            handler = VNCLoggingHandler(vnc_logger)
            
            # 设置日志格式（简化格式，因为 VNC 前端会显示时间戳）
            formatter = logging.Formatter('[%(name)s] %(message)s')
            handler.setFormatter(formatter)
            
            # 添加到 root logger
            root_logger = logging.getLogger()
            
            # ✅ 强制设置日志级别为 INFO（确保捕获所有 INFO 及以上级别的日志）
            # 这很重要，因为某些库（如 BrowserUse）可能会修改日志级别
            root_logger.setLevel(logging.INFO)
            
            # 添加我们的 handler
            root_logger.addHandler(handler)
            
            # 首先保存原始的 print 函数（在拦截之前）
            import builtins
            original_print = builtins.print
            
            # ✅ 确保 BrowserUse 的父 logger 使用 INFO 级别
            # BrowserUse 使用的实际 logger 名称如：
            #   - browser_use.agent.service
            #   - browser_use.tools.service  
            #   - browser_use.{self}
            # 配置父 logger 'browser_use' 让所有子 logger 继承
            browser_use_logger = logging.getLogger('browser_use')
            browser_use_logger.setLevel(logging.INFO)
            
            # 🔧 关键修复：强制设置 propagate=True
            # BrowserUse 的 logging_config.py 会设置 propagate=False（第 161 行）
            # 这会阻止日志传播到 root logger，导致我们的 VNCLoggingHandler 无法捕获
            # 我们必须在每次创建 logger 时都强制设置为 True
            browser_use_logger.propagate = True
            
            # 额外检查：确认 propagate 确实生效
            if not browser_use_logger.propagate:
                original_print(f"⚠️  警告：无法设置 browser_use.propagate=True，日志可能无法捕获")
            else:
                original_print(f"✅ BrowserUse logger 配置完成 (propagate={browser_use_logger.propagate})")
                
            # 拦截 print 输出
            # 注意：这会影响所有 print() 调用
            
            def logging_print(*args, **kwargs):
                # 先调用原始 print
                original_print(*args, **kwargs)
                # 然后记录到 logging
                message = ' '.join(str(arg) for arg in args)
                if message.strip():  # 忽略空行
                    logging.getLogger("print").info(message)
            
            builtins.print = logging_print
            
            original_print(f"✅ Python logging 拦截已启用 - 所有日志将转发到 VNC Viewer")
        except Exception as e:
            print(f"⚠️  启用 Python logging 拦截失败: {e}")
    
    return vnc_logger


def print_and_log(message: str, level: str = "INFO"):
    """
    同时打印到控制台和使用 Python logging 记录
    
    Args:
        message: 消息内容
        level: 日志级别 (INFO, DEBUG, WARNING, ERROR)
    
    示例：
        print_and_log("🚀 开始执行任务")
        print_and_log("⚠️ 警告信息", level="WARNING")
    """
    # 打印到控制台
    print(message)
    
    # 使用 Python logging 记录（会被拦截器转发到 VNC）
    logger = logging.getLogger("example")
    level_func = getattr(logger, level.lower(), logger.info)
    level_func(message)


def print_section(title: str, width: int = 60):
    """
    打印分隔线标题
    
    Args:
        title: 标题文本
        width: 总宽度
    
    示例：
        print_section("步骤 1: 创建 Sandbox")
        # 输出：
        # ============================================================
        # 步骤 1: 创建 Sandbox
        # ============================================================
    """
    separator = "=" * width
    message = f"\n{separator}\n{title}\n{separator}"
    print(message)
    
    # 使用 Python logging 记录（会被拦截器转发到 VNC）
    logging.getLogger("example").info(f"{title}")


def print_info(label: str, value: Any, indent: int = 3):
    """
    打印信息（键值对）
    
    Args:
        label: 标签
        value: 值
        indent: 缩进空格数
    
    示例：
        print_info("Sandbox ID", "sandbox-123")
        # 输出：   Sandbox ID: sandbox-123
    """
    message = f"{' ' * indent}{label}: {value}"
    print(message)
    logging.getLogger("example").info(message)


def print_result(result: str, width: int = 60):
    """
    打印结果（带边框）
    
    Args:
        result: 结果文本
        width: 边框宽度
    
    示例：
        print_result("任务执行成功")
        # 输出：
        # ------------------------------------------------------------
        # 任务执行成功
        # ------------------------------------------------------------
    """
    print("\n" + "-" * width)
    print(result)
    print("-" * width)
    
    # 同时记录到 logging
    logging.getLogger("example").info(f"📊 结果: {result}")


def get_env_or_default(key: str, default: str) -> str:
    """
    获取环境变量，如果不存在则返回默认值
    
    Args:
        key: 环境变量名
        default: 默认值
    
    Returns:
        环境变量值或默认值
    
    示例：
        user_id = get_env_or_default("USER_ID", "default_user")
    """
    return os.getenv(key, default)


def validate_settings(settings) -> bool:
    """
    验证必要的配置是否完整
    
    Args:
        settings: 配置对象（来自 config.get_settings()）
    
    Returns:
        True 如果配置完整，False 否则
    
    示例：
        from config import get_settings
        settings = get_settings()
        if not validate_settings(settings):
            print("配置不完整")
            return
    """
    if not settings.dashscope_api_key or "your-dashscope" in settings.dashscope_api_key:
        print("\n❌ 错误：请先配置 DASHSCOPE_API_KEY")
        print("   1. 复制 env.example 为 .env")
        print("   2. 访问 https://dashscope.console.aliyun.com/ 获取 API Key")
        print("   3. 在 .env 文件中填入 API Key")
        return False
    return True


def print_example_header(
    title: str,
    description: str = None,
    estimated_time: str = None,
    width: int = 60
):
    """
    打印示例的标准头部
    
    Args:
        title: 示例标题
        description: 示例描述（可选）
        estimated_time: 预计耗时（可选）
        width: 宽度
    
    示例：
        print_example_header(
            "示例 1: 基础用法",
            description="展示如何使用 BrowserUse 执行简单任务",
            estimated_time="1-3 分钟"
        )
    """
    print("\n" + "=" * width)
    print(title)
    print("=" * width)
    
    if description:
        print(f"\n📚 本示例展示：")
        for line in description.split('\n'):
            if line.strip():
                print(f"   {line.strip()}")
    
    if estimated_time:
        print(f"\n⏱️  预计耗时：{estimated_time}")
    
    print()


def print_sandbox_info(sandbox: Dict[str, Any], show_urls: bool = True):
    """
    打印 Sandbox 信息
    
    Args:
        sandbox: Sandbox 信息字典
        show_urls: 是否显示完整的 URL
    
    示例：
        sandbox = create_or_get_sandbox(...)
        print_sandbox_info(sandbox)
    """
    print(f"\n📋 Sandbox 信息：")
    print_info("Sandbox ID", sandbox['sandbox_id'])
    
    if show_urls:
        cdp_url = sandbox['cdp_url']
        if len(cdp_url) > 60:
            cdp_url = cdp_url[:60] + "..."
        print_info("CDP URL", cdp_url)
        
        if sandbox.get('vnc_url'):
            vnc_url = sandbox['vnc_url']
            if len(vnc_url) > 60:
                vnc_url = vnc_url[:60] + "..."
            print_info("VNC URL", vnc_url)
    
    print_info("Is New", "✅ 新创建" if sandbox.get('is_new') else "♻️  复用")


def print_vnc_info(viewer_url: str):
    """
    打印 VNC Viewer 信息
    
    Args:
        viewer_url: VNC Viewer URL
    
    示例：
        viewer_url = get_vnc_viewer_url(sandbox_id)
        print_vnc_info(viewer_url)
    """
    print(f"\n🖥️  VNC Viewer:")
    print(f"   {viewer_url}")
    print(f"   💡 提示：可以在浏览器中实时查看操作过程")


def print_execution_stats(
    result,
    show_tokens: bool = True,
    show_thoughts: bool = True,
    max_thoughts: int = 3
):
    """
    打印任务执行统计信息
    
    Args:
        result: BrowserUse Agent 的执行结果
        show_tokens: 是否显示 Token 使用情况
        show_thoughts: 是否显示思考过程
        max_thoughts: 最多显示几条思考记录
    
    示例：
        result = await agent.run()
        print_execution_stats(result)
    """
    print(f"\n📈 执行统计：")
    
    # 步骤数
    thoughts = result.model_thoughts()
    print_info("步骤数", len(thoughts))
    
    # Token 使用情况
    if show_tokens:
        try:
            if hasattr(result, 'input_tokens'):
                print_info("输入 Token", result.input_tokens)
            if hasattr(result, 'output_tokens'):
                print_info("输出 Token", result.output_tokens)
            if hasattr(result, 'total_tokens'):
                print_info("总 Token", result.total_tokens)
        except Exception:
            pass
    
    # 模型思考过程
    if show_thoughts and thoughts:
        print(f"\n🤔 模型思考过程（前 {min(max_thoughts, len(thoughts))} 步）：")
        for i, thought in enumerate(thoughts[:max_thoughts], 1):
            thought_text = str(thought.model_dump().get('thought', 'N/A'))
            if len(thought_text) > 100:
                thought_text = thought_text[:100] + "..."
            print(f"   {i}. {thought_text}")


def setup_example_environment():
    """
    设置示例代码的运行环境
    
    功能：
    - 加载 .env 文件
    - 设置日志级别
    - 添加项目路径到 sys.path
    
    示例：
        setup_example_environment()
    """
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    
    # 设置日志级别
    os.environ.setdefault('BROWSER_USE_LOGGING_LEVEL', 'info')
    
    # ✅ 预配置 Python logging，确保 BrowserUse 导入时使用我们的配置
    root_logger = logging.getLogger()
    
    # 🔧 关键修复：添加一个 dummy handler 到 root logger
    # BrowserUse 的 setup_logging() 会检查 hasHandlers()
    # 如果为 True，则会提前返回，不会清空我们的配置或设置 propagate=False
    if not root_logger.hasHandlers():
        dummy_handler = logging.NullHandler()
        root_logger.addHandler(dummy_handler)
        print(f"✅ 添加 dummy handler 以阻止 BrowserUse 覆盖日志配置")
    
    # 强制设置日志级别为 INFO
    root_logger.setLevel(logging.INFO)
    
    # ✅ 修复：配置父 logger 'browser_use'，而不是单独的子 logger
    # BrowserUse 使用的实际 logger 名称是：
    #   - browser_use.agent.service
    #   - browser_use.tools.service
    #   - browser_use.{self}  (动态)
    # 配置父 logger 可以让所有子 logger 继承设置
    browser_use_logger = logging.getLogger('browser_use')
    browser_use_logger.setLevel(logging.INFO)
    browser_use_logger.propagate = True
    
    # 添加项目根目录到 Python 路径（已在模块顶部处理）


__all__ = [
    # Logger - 只提供基础日志方法
    "create_logger",
    
    # 工具函数
    "setup_example_environment",
    "validate_settings",
    "get_env_or_default",
    
    # 打印工具（可选使用）
    "print_section",
    "print_info",
    "print_result",
    "print_sandbox_info",
    "print_vnc_info",
    "print_execution_stats",
    "print_example_header",
]

