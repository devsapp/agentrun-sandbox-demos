"""
Sandbox 生命周期：创建与删除

依赖：agentrun-sdk，使用前需配置 .env（AIO_TEMPLATE_NAME、阿里云 AK/SK、Region）。
"""

import os
import re
from typing import Any, Tuple

from dotenv import load_dotenv

load_dotenv()
# SDK 使用 AGENTRUN_* 命名，与 .env 中常见的 ALIBABA_CLOUD_* 做同步
if not os.getenv("AGENTRUN_ACCOUNT_ID") and os.getenv("ALIBABA_CLOUD_ACCOUNT_ID"):
    os.environ["AGENTRUN_ACCOUNT_ID"] = os.environ["ALIBABA_CLOUD_ACCOUNT_ID"]
if not os.getenv("AGENTRUN_REGION") and os.getenv("ALIBABA_CLOUD_REGION"):
    os.environ["AGENTRUN_REGION"] = os.environ["ALIBABA_CLOUD_REGION"]


def create_sandbox(
    template_name: str | None = None,
    idle_timeout_seconds: int = 1800,
) -> Tuple[Any, str, str | None]:
    """
    创建 AIO Sandbox（需已存在对应 Template）。

    Args:
        template_name: 模板名称，为 None 时从环境变量 AIO_TEMPLATE_NAME 读取
        idle_timeout_seconds: 空闲超时秒数

    Returns:
        (sandbox, sandbox_id, base_url)
        base_url 为 Sandbox HTTP 基础 URL，用于 /contexts/execute 等；解析失败时为 None
    """
    from agentrun.sandbox import Sandbox, TemplateType

    if template_name is None:
        template_name = os.getenv("AIO_TEMPLATE_NAME", "your-aio-template")

    sandbox = Sandbox.create(
        template_type=TemplateType.AIO,
        template_name=template_name,
        sandbox_idle_timeout_seconds=idle_timeout_seconds,
    )
    sandbox_id = sandbox.sandbox_id
    base_url = _get_base_url(sandbox, sandbox_id)
    return sandbox, sandbox_id, base_url


def _get_base_url(sandbox: Any, sandbox_id: str) -> str | None:
    """从 sandbox 的 CDP URL 解析 HTTP base URL。"""
    try:
        cdp_url = sandbox.get_cdp_url() if hasattr(sandbox, "get_cdp_url") else None
    except Exception:
        cdp_url = None
    if not cdp_url or not cdp_url.startswith("ws"):
        return None
    match = re.search(r"wss?://(.+?)/sandboxes/(.+?)/", cdp_url)
    if match:
        domain, sid = match.group(1), match.group(2)
        return f"https://{domain}/sandboxes/{sid}"
    return None


def destroy_sandbox(sandbox: Any) -> None:
    """
    释放远程 Sandbox 并建议调用方清理本地引用。

    按优先级尝试：delete() -> stop() -> destroy()。
    调用后不应再使用该 sandbox 对象。
    """
    if sandbox is None:
        return
    try:
        if hasattr(sandbox, "delete"):
            sandbox.delete()
        elif hasattr(sandbox, "stop"):
            sandbox.stop()
        elif hasattr(sandbox, "destroy"):
            sandbox.destroy()
    finally:
        pass  # 调用方负责将本地 sandbox 引用置为 None
