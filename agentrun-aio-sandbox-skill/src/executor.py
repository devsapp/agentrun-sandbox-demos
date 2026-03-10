"""
在 Sandbox 内执行 Python 代码（HTTP API）

需传入 Sandbox 的 HTTP base_url（创建 Sandbox 后由 sandbox_lifecycle 提供）。
"""

import json
from typing import Any

import httpx


def execute_python_code(
    base_url: str,
    code: str,
    context_id: str | None = None,
    timeout_ms: int = 300000,
) -> dict[str, Any]:
    """
    在 Sandbox 中执行 Python 代码（POST /contexts/execute）。

    Args:
        base_url: Sandbox HTTP 基础 URL，如 https://xxx/sandboxes/xxx
        code: Python 代码字符串
        context_id: 可选，同一 context 内多次执行保持变量
        timeout_ms: 执行超时毫秒数

    Returns:
        {
            "executionId": str,
            "status": "completed" | "failed",
            "result": {"exitCode": int, "stdout": str, "stderr": str},
        }
    """
    url = f"{base_url.rstrip('/')}/contexts/execute"
    payload = {"code": code, "timeout": timeout_ms}
    if context_id:
        payload["contextId"] = context_id
    else:
        payload["language"] = "python"

    with httpx.Client(timeout=float(timeout_ms) / 1000 + 10) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        raw = resp.json()

    execution_id = raw.get("contextId", "")
    results = raw.get("results", [])
    stdout_parts = []
    stderr_parts = []
    error_parts = []
    has_error = False
    for item in results:
        t = item.get("type", "")
        if t == "stdout":
            stdout_parts.append(item.get("text", ""))
        elif t == "stderr":
            stderr_parts.append(item.get("text", ""))
        elif t == "error":
            has_error = True
            error_parts.append(item.get("value", ""))

    stdout = "\n".join(stdout_parts)
    stderr = "\n".join(stderr_parts) + "\n".join(error_parts)
    status = "failed" if has_error else "completed"
    exit_code = 1 if has_error else 0

    return {
        "executionId": execution_id,
        "status": status,
        "result": {
            "exitCode": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        },
    }


def execute_shell_command(
    base_url: str,
    command: str,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """
    在 Sandbox 中执行 Shell 命令（POST /processes/cmd）。

    适用于需在后台常驻的进程（如 HTTP 服务）：可用 nohup ... & 让命令立即返回。

    Args:
        base_url: Sandbox HTTP 基础 URL
        command: Shell 命令字符串
        timeout: 请求超时秒数

    Returns:
        {
            "status": "completed" | "failed",
            "result": {"exitCode": int, "stdout": str, "stderr": str},
        }
    """
    url = f"{base_url.rstrip('/')}/processes/cmd"
    payload = {"command": command}

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        result = resp.json()

    if "result" in result:
        r = result["result"]
        exit_code = r.get("exitCode", -1)
        status = "completed" if exit_code == 0 else "failed"
        return {
            "status": status,
            "result": {
                "exitCode": exit_code,
                "stdout": r.get("stdout", ""),
                "stderr": r.get("stderr", ""),
            },
        }
    return {
        "status": "failed",
        "result": {"exitCode": -1, "stdout": "", "stderr": result.get("message", "unknown")},
    }
