"""
配置管理模块 - 统一管理所有环境变量和配置
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings(BaseModel):
    """应用配置"""
    
    # DashScope API 配置
    dashscope_api_key: str = Field(
        default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""),
        description="DashScope API Key"
    )
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="DashScope API 基础 URL"
    )
    qwen_model: str = Field(
        default="qwen-vl-max",
        description="Qwen 模型名称"
    )
    
    # 阿里云访问密钥
    alibaba_cloud_access_key_id: str = Field(
        default_factory=lambda: os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", ""),
        description="阿里云 Access Key ID"
    )
    alibaba_cloud_access_key_secret: str = Field(
        default_factory=lambda: os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", ""),
        description="阿里云 Access Key Secret"
    )
    alibaba_cloud_account_id: str = Field(
        default_factory=lambda: os.getenv("ALIBABA_CLOUD_ACCOUNT_ID", ""),
        description="阿里云账号 ID"
    )
    alibaba_cloud_region: str = Field(
        default="cn-hangzhou",
        description="阿里云地域"
    )
    
    # Sandbox 配置
    sandbox_idle_timeout: int = Field(
        default=600,
        description="Sandbox 空闲超时时间（秒）"
    )
    
    # BrowserUse 配置
    browser_timeout: int = Field(
        default=3000000,
        description="浏览器超时（毫秒）"
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        description="User Agent"
    )
    browser_headless: bool = Field(
        default=False,
        description="是否启用无头模式"
    )
    browser_use_vision: bool = Field(
        default=True,
        description="是否启用视觉能力"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


if __name__ == "__main__":
    # 测试配置加载
    settings = get_settings()
    print("配置加载成功！")
    print(f"Model: {settings.qwen_model}")
    print(f"Region: {settings.alibaba_cloud_region}")
    print(f"Browser Headless: {settings.browser_headless}")

