# LangChain + AgentRun Browser Sandbox 集成示例

这是一个完整的示例项目，演示如何使用 LangChain 手动创建 Browser Sandbox 相关的 tools，并集成 VNC 可视化功能。

## 功能特性

- 使用纯 LangChain 实现，手动创建 Sandbox tools
- 支持 OpenAI 兼容的 API（DashScope）
- 完整的 Sandbox 生命周期管理
- VNC 可视化集成
- 模块化设计，代码内聚
- 中文友好的提示词和输出
- 自动资源清理（支持 Ctrl+C 中断）

##  项目结构

```
langchain-with-agentrun-demo/
├── README.md                    # 项目说明文档（本文档）
├── requirements.txt             # Python 依赖包列表
├── env.example                  # 环境变量配置示例
│
├── main.py                      # 主入口文件（包含 VNC 自动打开）
├── langchain_agent.py           # LangChain Agent 和 Tools 注册模块
├── sandbox_manager.py           # Sandbox 生命周期管理模块
└── vnc.html                     # VNC 查看器（本地测试用）
```

### 核心模块说明

| 模块 | 职责 | 说明 |
|------|------|------|
| `main.py` | 主入口 | 演示如何使用 LangChain Agent，包含自动打开 VNC 查看器功能 |
| `langchain_agent.py` | Agent 和 Tools | 负责创建 LangChain tools 和 Agent，集成 VNC 信息 |
| `sandbox_manager.py` | Sandbox 管理 | 负责 Sandbox 的创建、管理和销毁，提供统一的接口 |
| `vnc.html` | VNC 查看器 | 本地 VNC 可视化界面，支持实时查看浏览器操作 |

## 快速开始

### 1. 环境准备

#### 系统要求

- **Python 版本**：Python 3.10+（推荐 3.12）
- **操作系统**：macOS / Linux / Windows

#### 安装 uv（推荐）

`uv` 是一个快速、可靠的 Python 包管理器，推荐使用。

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew (macOS)
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

更多安装方式请参考：https://docs.astral.sh/uv/getting-started/installation/

### 2. 克隆项目

```bash
# 克隆项目
git clone <repository-url>
cd langchain-with-agentrun-demo
```

### 3. 创建虚拟环境并安装依赖

#### 方式 1：使用 uv（推荐）⭐

```bash
# 创建 Python 3.12 虚拟环境
uv venv .venv --python 3.12

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# 安装依赖
uv pip install -r requirements.txt
```

> **uv 优势**：
> - **速度快**：比 pip 快 10-100 倍
> - **可靠**：内置依赖解析和锁定
> - **简单**：统一的命令行接口

#### 方式 2：使用传统 pip

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `env.example` 为 `.env` 并填入您的凭证：

```bash
cp env.example .env
```

编辑 `.env` 文件（**必须配置**）：

```bash
# =============================================================================
# DashScope API 配置（必需）
# =============================================================================
# 获取 API Key: https://bailian.console.aliyun.com/?tab=app#/api-key
DASHSCOPE_API_KEY=sk-your-bailian-api-key

# Qwen 模型名称（可选，默认 qwen-plus）
QWEN_MODEL=qwen-plus

# =============================================================================
# 阿里云访问密钥（必需）
# =============================================================================
# 获取方式：https://ram.console.aliyun.com/manage/ak
ALIBABA_CLOUD_ACCESS_KEY_ID=your-access-key-id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-access-key-secret
ALIBABA_CLOUD_ACCOUNT_ID=your-main-account-id
ALIBABA_CLOUD_REGION=cn-hangzhou

# =============================================================================
# Sandbox 配置（必需）
# =============================================================================
# browser sandbox 模板的名称
# 可以在 https://functionai.console.aliyun.com/cn-hangzhou/agent/runtime/sandbox 控制台创建
BROWSER_TEMPLATE_NAME=sandbox-your-template-name

# =============================================================================
# AgentRun 端点配置（可选）
# =============================================================================
# agentrun 的控制面和数据面的 API 端点请求地址
AGENTRUN_CONTROL_ENDPOINT=agentrun.cn-hangzhou.aliyuncs.com
AGENTRUN_DATA_ENDPOINT=https://${your-main-account-id}.agentrun-data.cn-hangzhou.aliyuncs.com
```

### 5. 运行示例

#### 方式 1：使用 uv（推荐）

```bash
# 确保虚拟环境已激活
source .venv/bin/activate  # macOS/Linux

# 使用 uv 运行
uv run main.py
```

#### 方式 2：使用传统 python

```bash
# 确保虚拟环境已激活
source .venv/bin/activate  # macOS/Linux

# 运行主程序
python main.py
```

程序会：
1. 初始化 LangChain Agent
2. 执行预设的示例查询
3. **自动打开 VNC 查看器**（在浏览器中实时查看操作）
4. 进入交互模式，可以输入自定义查询

**退出方式**：
- 输入 `quit` 或 `exit` 退出
- 按 `Ctrl+C` 中断（会自动清理资源）

## 核心功能详解

### 1. Sandbox 管理器 (`sandbox_manager.py`)

负责 Sandbox 生命周期管理，提供统一的接口。

#### 基本用法

```python
from sandbox_manager import SandboxManager

# 创建管理器
manager = SandboxManager()

# 创建 Sandbox
info = manager.create(template_name="sandbox-browser-demo")
print(f"Sandbox ID: {info['sandbox_id']}")
print(f"CDP URL: {info['cdp_url']}")
print(f"VNC URL: {info['vnc_url']}")

# 获取信息
info = manager.get_info()

# 检查状态
if manager.is_active():
    print("Sandbox 运行中")

# 销毁 Sandbox
manager.destroy()
```

#### 独立测试

您可以单独测试 Sandbox 的创建、使用和销毁：

```bash
# 使用 uv 运行
uv run sandbox_manager.py

# 或使用 python
python sandbox_manager.py
```

测试会执行：
1. 创建 Sandbox
2. 获取 Sandbox 信息（包括 VNC URL）
3. 尝试连接浏览器（如果安装了 Playwright）
4. 检查 Sandbox 状态
5. 销毁 Sandbox

### 2. LangChain Agent (`langchain_agent.py`)

负责创建 LangChain tools 和 Agent，实现浏览器自动化功能。

#### 可用的 Tools

| Tool 名称 | 功能 | 说明 |
|----------|------|------|
| `create_browser_sandbox` | 创建或获取浏览器 Sandbox | 返回 Sandbox ID、CDP URL、VNC URL |
| `get_sandbox_info` | 获取当前 Sandbox 的详细信息 | 包括 ID、CDP URL、VNC URL |
| `navigate_to_url` | 导航到指定 URL | 使用 Playwright 连接 CDP URL |
| `take_screenshot` | 截取页面截图 | 保存为本地文件 |
| `destroy_sandbox` | 销毁 Sandbox 实例 | 释放资源（仅在明确需要时使用）|

#### 创建 Agent

```python
from langchain_agent import create_browser_agent, get_sandbox_manager

# 创建 Agent
agent = create_browser_agent()

# 使用 Agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "创建一个浏览器 sandbox"}]
})

# 获取 Sandbox 管理器
manager = get_sandbox_manager()
```

#### 自定义系统提示词

```python
custom_prompt = """你是一个专业的网页数据提取助手...
"""

agent = create_browser_agent(system_prompt=custom_prompt)
```

### 3. VNC 可视化

#### 自动打开 VNC 查看器

运行 `main.py` 后，程序会自动打开 VNC 查看器：

1. 启动本地 HTTP 服务器（默认端口 8080）
2. 自动在浏览器中打开 `vnc.html`
3. 自动填充 VNC URL 并连接
4. 实时查看浏览器操作

#### 手动使用 VNC 查看器

如果自动打开失败，可以手动操作：

```bash
# 方式 1: 直接打开 HTML 文件
# macOS
open vnc.html

# Linux
xdg-open vnc.html

# 方式 2: 使用 Python HTTP 服务器
python -m http.server 8000
# 然后访问 http://localhost:8000/vnc.html
```

手动输入 VNC URL 后点击"连接"按钮。

#### 获取 VNC URL

**方式 1：通过测试脚本获取**

```bash
uv run sandbox_manager.py
# 输出中会显示 VNC URL
```

**方式 2：通过 Agent 调用**

```python
result = agent.invoke({
    "messages": [{"role": "user", "content": "获取 sandbox 信息"}]
})
```

**方式 3：直接通过管理器获取**

```python
from langchain_agent import get_sandbox_manager

manager = get_sandbox_manager()
info = manager.get_info()
vnc_url = info['vnc_url']
```

## 使用示例

### 示例 1: 基础浏览器操作

```python
from langchain_agent import create_browser_agent

# 创建 Agent
agent = create_browser_agent()

# 示例查询
queries = [
    "创建一个浏览器 sandbox",
    "获取当前 sandbox 的信息，包括 VNC URL",
    "导航到 https://www.aliyun.com",
    "截取当前页面截图",
]

for query in queries:
    result = agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    output = result.get("messages", [])[-1].content
    print(f"结果: {output}")
```

### 示例 2: 使用上下文管理器

```python
from sandbox_manager import SandboxManager

# 使用上下文管理器自动清理
with SandboxManager() as manager:
    info = manager.create()
    print(f"Sandbox ID: {info['sandbox_id']}")
    
    # 使用 Sandbox...
    
    # 自动销毁
```

### 示例 3: 完整的网页数据提取流程

```python
from langchain_agent import create_browser_agent

# 创建 Agent
agent = create_browser_agent()

# 执行任务
task = """
1. 创建一个浏览器 sandbox
2. 访问 https://www.aliyun.com
3. 提取页面的主要产品分类
4. 截取页面截图
"""

result = agent.invoke({
    "messages": [{"role": "user", "content": task}]
})

print(result.get("messages", [])[-1].content)
```

## 工作原理

1. **工具注册**：使用 `@tool` 装饰器将 Sandbox 功能封装为 LangChain tools
2. **生命周期管理**：`SandboxManager` 负责 Sandbox 的创建、管理和销毁
3. **状态保持**：使用单例模式管理 Sandbox 实例，确保同一会话内复用
4. **VNC 集成**：自动获取并返回 VNC URL，方便用户实时查看
5. **错误处理**：所有工具都包含完善的错误处理机制
6. **资源清理**：
   - 显式清理：`finally` 块中的 `destroy_sandbox()`
   - 信号处理：捕获 `Ctrl+C` (SIGINT) 和 `Ctrl+D` (EOF)
   - atexit 兜底：程序退出时自动清理

## 最佳实践

### 1. 资源管理

#### 推荐做法

```python
from langchain_agent import create_browser_agent, get_sandbox_manager

try:
    agent = create_browser_agent()
    
    # 执行任务...
    
finally:
    # 确保清理资源
    manager = get_sandbox_manager()
    if manager.is_active():
        manager.destroy()
```

#### 不推荐

```python
# 不要在每轮对话后都销毁 sandbox
agent.invoke({"messages": [...]})
manager.destroy()  # 不推荐：应该在程序退出时销毁

agent.invoke({"messages": [...]})
# 错误：sandbox 已经被销毁，无法继续使用
```

### 2. 错误处理

```python
from langchain_agent import create_browser_agent

agent = create_browser_agent()

try:
    result = agent.invoke({
        "messages": [{"role": "user", "content": "访问网页"}]
    })
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"执行失败: {e}")
```

### 3. 自定义工具

您可以轻松添加更多工具：

```python
from langchain.tools import tool

@tool
def click_element(selector: str) -> str:
    """点击页面元素
    
    Args:
        selector: CSS 选择器
    
    Returns:
        操作结果
    """
    # 实现点击逻辑
    pass

@tool
def extract_text(selector: str) -> str:
    """提取页面文本
    
    Args:
        selector: CSS 选择器
    
    Returns:
        提取的文本
    """
    # 实现文本提取逻辑
    pass
```

### 4. 环境变量管理

#### 推荐做法

```python
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")
```

#### 不推荐

```python
# 不要硬编码敏感信息
api_key = "sk-xxxxx"  # 不要这样做！
```

### 5. VNC 使用建议

- 开发调试时启用 VNC，实时查看操作
- 生产环境可以禁用 VNC（节省资源）
- 使用本地 HTTP 服务器提供 VNC 页面（更稳定）
- 不要在 VNC URL 中包含敏感信息

## 故障排查

### 环境配置问题

#### API Key 错误

```bash
# 验证 DashScope API Key
curl -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
     https://dashscope.aliyuncs.com/compatible-mode/v1/models

# 检查环境变量是否正确加载
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DASHSCOPE_API_KEY'))"
```

#### 阿里云访问密钥错误

```bash
# 检查环境变量
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(f'AK ID: {os.getenv(\"ALIBABA_CLOUD_ACCESS_KEY_ID\", \"未设置\")[:10]}...')
print(f'AK Secret: {os.getenv(\"ALIBABA_CLOUD_ACCESS_KEY_SECRET\", \"未设置\")[:10]}...')
print(f'Account ID: {os.getenv(\"ALIBABA_CLOUD_ACCOUNT_ID\", \"未设置\")}')
"
```

### Sandbox 创建问题

#### Sandbox 创建失败

```bash
# 检查 agentrun SDK 是否正确安装
pip show agentrun-sdk

# 重新安装
uv pip install --upgrade agentrun-sdk[playwright,server]
# 或
pip install --upgrade agentrun-sdk[playwright,server]

# 检查模板名称是否正确
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(f'Template Name: {os.getenv(\"BROWSER_TEMPLATE_NAME\", \"未设置\")}')"
```

#### 连接超时

```bash
# 检查网络连接
ping agentrun.cn-hangzhou.aliyuncs.com

# 检查端点配置
echo $AGENTRUN_CONTROL_ENDPOINT
```

### VNC 问题

#### HTTP 服务器启动失败

```bash
# 检查端口是否被占用
lsof -i :8080

# 修改代码中的端口
# 在 main.py 中修改 _http_port = 8080 为其他端口
```

#### VNC 无法连接

```bash
# 检查 VNC URL 是否正确
python -c "
from sandbox_manager import SandboxManager
manager = SandboxManager()
info = manager.create()
print(f'VNC URL: {info.get(\"vnc_url\", \"未获取到\")}')"
```

### 依赖安装问题

#### uv 安装失败

```bash
# 方法 1：使用 pip 安装
pip install -r requirements.txt

# 方法 2：清理缓存后重试
uv cache clean
uv pip install -r requirements.txt

# 方法 3：指定镜像源（中国大陆用户）
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 虚拟环境问题

```bash
# 删除现有虚拟环境
rm -rf .venv

# 重新创建
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 运行时错误

#### 模块导入错误

```bash
# 确保虚拟环境已激活
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 确认 Python 路径
which python
python --version

# 重新安装依赖
uv pip install -r requirements.txt
```

### 获取帮助

如果以上方法无法解决问题，请：

1. 查看 [docs/](docs/) 目录中的详细文档
2. 参考 [AgentRun 文档中心](https://doc.agent.run/)
3. 通过 [AgentRun 控制台](https://functionai.console.aliyun.com/agent/explore) 提交工单

## 依赖说明

主要依赖：

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| `langchain` | >= 0.1.0 | LangChain 核心库 |
| `langchain-openai` | >= 0.0.5 | OpenAI 兼容的 LLM 接口 |
| `agentrun-sdk[playwright,server]` | >= 0.0.8 | AgentRun SDK（包含 Playwright 和 Server 扩展）|
| `playwright` | >= 1.40.0 | 浏览器自动化库 |
| `python-dotenv` | >= 1.0.0 | 环境变量管理 |

完整依赖列表请查看 `requirements.txt`。

### 参考资源

- [LangChain Tools 文档](https://docs.langchain.com/oss/python/langchain/tools)
- [AgentRun SDK 文档](https://github.com/alibaba/agentrun-sdk)
- [AgentRun 文档中心](https://doc.agent.run/)
- [AgentRun 控制台](https://functionai.console.aliyun.com/agent/explore)
- [阿里云百炼平台](https://dashscope.console.aliyun.com/)

## 技术支持

如有问题，请：

1. 查看本文档的故障排查章节
2. 查看 [docs/](docs/) 目录中的详细文档
3. 参考 [AgentRun 文档中心](https://doc.agent.run/)