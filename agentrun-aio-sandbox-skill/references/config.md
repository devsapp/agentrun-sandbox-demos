# AgentRun AIO Sandbox 敏感配置说明

使用本 Skill 前，必须配置以下敏感信息，且**不得提交到版本库**。

## 推荐方式

1. **`.env` 文件**（推荐）
   - 在项目根目录创建 `.env`，并确保 `.gitignore` 包含 `.env`。
   - 使用 `python-dotenv` 在程序入口加载：`load_dotenv()`。
2. **本地配置文件**
   - 如 `config.local.json` 或 `settings.local.py`，仅存在于本地，不提交。

## 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | 阿里云 Access Key ID（AK） | 从 [RAM 控制台](https://ram.console.aliyun.com/manage/ak) 创建 |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | 阿里云 Access Key Secret（SK） | 同上 |
| `ALIBABA_CLOUD_REGION` | 阿里云地域（SDK 读的是 `AGENTRUN_REGION`，本 Skill 会自动从该变量同步） | `cn-hangzhou`、`ap-southeast-1` 等 |
| `AGENTRUN_ACCOUNT_ID` 或 `ALIBABA_CLOUD_ACCOUNT_ID` | 阿里云主账号 ID（SDK 必填） | 可留空：本目录 `test_run.py` 会通过 STS GetCallerIdentity 自动获取（需安装 `alibabacloud_sts20150401`） |

## Sandbox 相关

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `AIO_TEMPLATE_NAME` | 已创建的 AIO 模板名称（创建 Sandbox 前需先在控制台建好） | `your-aio-template` |
| `SANDBOX_WILDCARD_DOMAIN` | Sandbox 泛域名，用于多端口域名生成 | `sandbox.example.com` |

## .env 示例

见本 Skill 的 `assets/env.example`。使用前复制为 `.env` 并填入真实值。

## 安全注意

- 不要将 `.env` 或含 AK/SK 的文件加入 Git。
- 生产环境建议使用密钥管理服务（如 KMS）或环境变量注入，而非本地文件。

## 常见问题：Read/Connect timeout 0.6s

若出现 `Read timed out. (read timeout=0.6)` 或 `connect timeout=0.06`，原因是 agentrun SDK 的 control API 在创建阿里云 OpenAPI 客户端时，把「秒」当成「毫秒」传给了底层（阿里云 Config 要求毫秒）。可修改 site-packages 中 `agentrun/utils/control_api.py` 的 `_get_client`：为 `AgentRunClient` 的 Config 传入 `read_timeout`，并将 `connect_timeout`/`read_timeout` 从秒转为毫秒（乘以 1000）再传入。完整验证流程见本目录根下的 `test_run.py`（创建 → 执行 → 8005 服务 → 泛域名 → 删除）。
