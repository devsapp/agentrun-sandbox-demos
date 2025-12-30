"""
VNC Logger - 客户端日志库
"""

import httpx
from datetime import datetime
from typing import Optional, Dict

class VNCLogger:
    """
    VNC Logger 客户端
    
    用法：
        logger = VNCLogger(session_id="xxx", server_url="http://localhost:8080")
        logger.info("消息")
    """
    
    def __init__(
        self,
        session_id: str,
        server_url: str = "http://localhost:8080"
    ):
        self.session_id = session_id
        self.server_url = server_url.rstrip('/')
        self.client = httpx.Client(timeout=5.0)
    
    def _send_log(self, level: str, message: str, extra: Optional[Dict] = None):
        """发送日志到服务器"""
        try:
            self.client.post(
                f"{self.server_url}/api/log/{self.session_id}",
                json={
                    "level": level,
                    "message": message,
                    "extra": extra or {}
                }
            )
        except Exception as e:
            # 静默失败，不影响业务逻辑
            pass
    
    def info(self, message: str, **kwargs):
        if message.startswith("[httpx] HTTP Request: POST http://localhost:8080/api/log/"):
            return  # 忽略 httpx 请求日志
        """普通信息日志"""
        self._send_log("INFO", f"ℹ️  {message}", kwargs if kwargs else None)
    
    def thinking(self, message: str, **kwargs):
        """AI 思考日志"""
        self._send_log("THINKING", f"💭 {message}", kwargs if kwargs else None)
    
    def action(self, message: str, **kwargs):
        """动作执行日志"""
        self._send_log("ACTION", f"⚡ {message}", kwargs if kwargs else None)
    
    def result(self, message: str, **kwargs):
        """结果日志"""
        self._send_log("RESULT", f"✅ {message}", kwargs if kwargs else None)
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        self._send_log("ERROR", f"❌ {message}", kwargs if kwargs else None)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._send_log("WARNING", f"⚠️  {message}", kwargs if kwargs else None)
    
    def step(self, message: str, **kwargs):
        """步骤日志"""
        self._send_log("STEP", f"📍 {message}", kwargs if kwargs else None)
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._send_log("DEBUG", f"🔍 {message}", kwargs if kwargs else None)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """关闭 logger"""
        self.client.close()

