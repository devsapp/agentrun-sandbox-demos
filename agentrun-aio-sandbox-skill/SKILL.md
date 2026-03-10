---
name: agentrun-aio-sandbox
description: AgentRun All-In-One (AIO) Sandbox 的创建、Python 代码执行、删除及多端口域名生成。在需要创建/管理阿里云 AgentRun AIO Sandbox、在 Sandbox 内执行 Python 代码、销毁 Sandbox 或按规则生成多端口访问域名时使用。使用前必须配置阿里云 AK/SK、Region 及 Sandbox 泛域名（见 references/config.md）。
---

# AgentRun AIO Sandbox

## 前置条件

1. **Template 先行**：AIO Sandbox 依赖已创建的 Template。在 [AgentRun 控制台](https://agentrun.ai/) 或通过 API 先创建好 AIO 类型模板，获得 `template_name`（如 `your-aio-template`）。
2. **敏感配置**：使用前必须配置阿里云与泛域名，**不要将敏感信息写进代码**。推荐方式：
   - 使用 `.env` 文件（如本目录 `assets/.env`），并加入 `.gitignore`；入口处用 `load_dotenv("assets/.env")` 或 `load_dotenv()` 加载。
   - SDK 读的是 `AGENTRUN_REGION`、`AGENTRUN_ACCOUNT_ID`；若 .env 里只配了 `ALIBABA_CLOUD_REGION`、`ALIBABA_CLOUD_ACCOUNT_ID`，需在加载 .env 后做同步（本目录 `src/sandbox_lifecycle.py` 与 `test_run.py` 已做同步；账号 ID 可留空时由 STS GetCallerIdentity 自动获取，需安装 `alibabacloud_sts20150401` 等）。
   - 变量说明与示例见 [references/config.md](references/config.md)。

## 1. 创建 AIO Sandbox

在 Template 已存在的前提下创建 Sandbox。源码见 `src/sandbox_lifecycle.py`。

```python
from dotenv import load_dotenv
from src.sandbox_lifecycle import create_sandbox

load_dotenv()
sandbox, sandbox_id, base_url = create_sandbox(idle_timeout_seconds=1800)
# 后续可用 sandbox.get_cdp_url()、sandbox.get_vnc_url() 等
```

或直接使用 SDK：

```python
import os
from dotenv import load_dotenv
from agentrun.sandbox import Sandbox, TemplateType

load_dotenv()
template_name = os.getenv("AIO_TEMPLATE_NAME", "your-aio-template")
sandbox = Sandbox.create(
    template_type=TemplateType.AIO,
    template_name=template_name,
    sandbox_idle_timeout_seconds=1800,
)
sandbox_id = sandbox.sandbox_id
```

- 执行代码或 HTTP 调用时需 Sandbox 的 **HTTP 基础 URL**：`create_sandbox` 会返回 `base_url`；若为空，可用 `https://{account_id}.agentrun-data.{region}.aliyuncs.com/sandboxes/{sandbox_id}` 拼接（`account_id` 取 `AGENTRUN_ACCOUNT_ID` 或 `ALIBABA_CLOUD_ACCOUNT_ID`，`region` 取 `AGENTRUN_REGION` 或 `ALIBABA_CLOUD_REGION`）。
- **创建后建议等待数秒**再调用 execute，避免实例未就绪导致 502；遇到 502 可重试 2～3 次。

## 2. 执行 Python 代码（execute_python_code）

在已创建的 Sandbox 上执行 Python 代码。源码见 `src/executor.py`。

**方式 A：HTTP API（本目录 `src/executor.py`）**

```python
from src.executor import execute_python_code

result = execute_python_code(base_url="https://...", code="print(1+1)", context_id=None)
# result 含 executionId, status, result.stdout/stderr/exitCode
```

**方式 B：SDK 异步执行**

若持有 `Sandbox` 实例：`result = await sandbox.context.execute_async(code="...", language="python")`。

- `context_id` 用于跨多次执行保持同一上下文。

## 2.1 执行 Shell 命令（execute_shell_command）

当需在 Sandbox 内执行 Shell 命令（如后台启动 HTTP 服务）时，使用 `execute_shell_command`（POST /processes/cmd）。适合需常驻的进程：用 `nohup ... &` 让命令立即返回。

```python
from src.executor import execute_shell_command

# 示例：在 8005 端口后台启动 HTML 服务（写 index.html 再起 http.server）
r = execute_shell_command(
    base_url="https://...",
    command="mkdir -p /tmp/www8005 && echo '<h1>OK</h1>' > /tmp/www8005/index.html && nohup python3 -m http.server 8005 --bind 0.0.0.0 --directory /tmp/www8005 > /tmp/srv8005.log 2>&1 & sleep 1 && echo done",
    timeout=20.0,
)
# r 含 status, result.exitCode/stdout/stderr
```

若 `execute_python_code` 无法满足在指定端口运行 HTTP 服务的需求，可改用 `execute_shell_command` 启动服务。

## 3. 删除 Sandbox

释放远程 Sandbox 并清理本地引用。源码见 `src/sandbox_lifecycle.py`。

```python
from src.sandbox_lifecycle import destroy_sandbox

destroy_sandbox(sandbox)  # 尝试 delete/stop/destroy，并清理引用
```

调用后不应再使用该 `sandbox` 对象或对应 `sandbox_id`。

## 4. 多端口域名生成

规则：`{端口}-{sandboxID}.{泛域名}`。源码见 `src/domain.py` 或 `scripts/sandbox_port_domain.py`。

```python
from src.domain import sandbox_port_domain

url = sandbox_port_domain(
    wildcard_domain="sandbox.example.com",
    port=8080,
    sandbox_id="sbx-abc123",
)
# → "8080-sbx-abc123.sandbox.example.com"
```

使用前从配置读取泛域名（如 `SANDBOX_WILDCARD_DOMAIN`）。配置方式见 [references/config.md](references/config.md)。

## 资源

- **敏感配置与变量说明**：[references/config.md](references/config.md)（含 control API 超时 0.6s 问题的处理说明）。
- **环境变量示例**：复制 `assets/env.example` 为 `.env`（建议放在 `assets/.env`），填入真实值并确保 `.env` 已加入 `.gitignore`。
- **源码**：`src/` 目录包含 `sandbox_lifecycle`（创建/删除）、`executor`（`execute_python_code` 与 `execute_shell_command`）、`domain`（多端口域名）。
- **一键验证**：在本目录执行 `python test_run.py` 可依次验证创建 → 执行 Python → execute_shell_command 在 8005 起 HTML 服务 → 输出泛域名 → 删除；运行前需配置 `assets/.env`。
- **多端口域名脚本**：`scripts/sandbox_port_domain.py` 可命令行调用：`python scripts/sandbox_port_domain.py <泛域名> <端口> <sandbox_id>`，或设置 `SANDBOX_WILDCARD_DOMAIN` 后传 `<端口> <sandbox_id>`。
