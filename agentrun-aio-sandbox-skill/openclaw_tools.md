# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

**说明**：本 Skill 的**工具定义、环境变量与使用流程均放在 tools.md**，便于 OpenClaw 在调用工具时统一感知环境变量与能力；若需单独约束 agent 行为或策略，可再在 agents.md 中补充。

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### Tavily

- API Key: xxx

---

## AgentRun AIO Sandbox

本 Skill 提供 Sandbox 创建、代码/Shell 执行、删除及预览域名生成。使用前在运行环境中加载下方环境变量（可从 `assets/.env` 或系统环境读取并在此处“定义”供 agent 感知）。

### 环境变量（定义与赋值）

调用本 Skill 前，确保以下变量已定义并赋值（可从 .env 加载或由 OpenClaw 运行环境注入）：

| 变量名 | 说明 | 赋值示例 / 来源 |
|--------|------|------------------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | 阿里云 AK | 从 .env 或环境读取 |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | 阿里云 SK | 从 .env 或环境读取 |
| `ALIBABA_CLOUD_REGION` | 地域（SDK 会同步为 AGENTRUN_REGION） | `cn-hangzhou` / `ap-southeast-1` |
| `AGENTRUN_ACCOUNT_ID` 或 `ALIBABA_CLOUD_ACCOUNT_ID` | 阿里云主账号 ID（SDK 必填） | 从 .env 或 STS 自动获取 |
| `AIO_TEMPLATE_NAME` | 已创建的 AIO 模板名称 | 如 `qianfeng-aio-sg` |
| `SANDBOX_WILDCARD_DOMAIN` | Sandbox 泛域名（预览域名生成用） | 如 `test.functioncompute.com` |

**赋值约定**：若使用 .env，在入口执行 `load_dotenv("assets/.env")` 或 `load_dotenv()`；Skill 内会将 `ALIBABA_CLOUD_REGION` 同步到 `AGENTRUN_REGION`、`ALIBABA_CLOUD_ACCOUNT_ID` 同步到 `AGENTRUN_ACCOUNT_ID`。

### 工具能力

- **create_sandbox**（template_name?, idle_timeout_seconds?）  
  创建 AIO Sandbox，返回 `(sandbox, sandbox_id, base_url)`。创建后建议等待数秒再执行代码；后续 execute 需使用 `base_url`。

- **execute_python_code**（base_url, code, context_id?, timeout_ms?）  
  在 Sandbox 内执行 Python 代码。返回 `executionId`、`status`、`result.stdout/stderr/exitCode`。

- **execute_shell_command**（base_url, command, timeout?）  
  在 Sandbox 内执行 Shell 命令；适合用 `nohup ... &` 后台起 HTTP 服务等。

- **destroy_sandbox**（sandbox）  
  释放远程 Sandbox，清理引用。

- **generate_preview_domain**（wildcard_domain, port, sandbox_id）  
  按规则生成该端口的预览域名：`{port}-{sandbox_id}.{wildcard_domain}`，返回不含协议的域名字符串；访问用 `https://{返回的域名}`。  
  `wildcard_domain` 使用环境变量 `SANDBOX_WILDCARD_DOMAIN` 的取值。

### 运行程序时的预览域名流程

当需要运行会监听端口的程序（如 HTTP 服务、Web 应用）时：

1. **随机生成监听端口**：在合理范围（如 8000～9999）随机选一个端口，作为程序在 Sandbox 内的监听端口，并在启动命令中使用该端口（通过 execute_shell_command 执行，如 `nohup python3 -m http.server <port> --bind 0.0.0.0 ... &`）。
2. **感知环境变量**：读取 `SANDBOX_WILDCARD_DOMAIN` 与当前会话的 `sandbox_id`（来自 create_sandbox 返回值）。
3. **调用预览域名生成**：用上述端口、`sandbox_id`、`SANDBOX_WILDCARD_DOMAIN` 调用 **generate_preview_domain**，得到该端口的预览域名。
4. **返回给用户**：将 `https://{生成的预览域名}` 返回给用户；并说明需泛域名已解析到该 Sandbox 才能访问，若看到「Welcome to OpenResty」等默认页表示网关尚未转发该端口。

**小结**：需要跑带端口的程序 → 随机端口 → 用该端口启动程序 → 读环境变量 + sandbox_id → 调 generate_preview_domain → 把 `https://{预览域名}` 给用户。

---

Add whatever helps you do your job. This is your cheat sheet.
