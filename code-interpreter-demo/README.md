# AgentRun Code Interpreter Sandbox 代码执行示例

这是一个演示如何使用 AgentRun Code Interpreter Sandbox 创建 sandbox 并执行代码的示例项目。

## 功能特性

- 使用过程式代码风格，简洁明了
- 支持创建新的 Code Interpreter Sandbox
- 支持连接到已存在的 Sandbox
- 代码执行上下文管理（变量状态保持）
- 自动资源清理

## 项目结构

```
.
├── README.md              # 项目说明文档（本文档）
├── requirements.txt       # Python 依赖包列表
├── env.example            # 环境变量配置示例
└── code_exec.py           # 代码执行示例（主文件）
```

### 核心文件说明

| 文件 | 职责 | 说明 |
|------|------|------|
| `code_exec.py` | 代码执行示例 | 演示如何创建 sandbox、执行代码、销毁 sandbox |

## 快速开始

### 1. 环境准备

#### 系统要求

- **Python 版本**：Python 3.10+（推荐 3.12）
- **操作系统**：macOS / Linux / Windows

#### 安装 uv（推荐）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew (macOS)
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 创建虚拟环境并安装依赖

```bash
# 创建 Python 3.12 虚拟环境
uv venv .venv --python 3.12

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `env.example` 为 `.env` 并填入您的凭证：

```bash
cp env.example .env
```

编辑 `.env` 文件（**必须配置**）：

```bash
# 阿里云访问密钥（必需）
ALIBABA_CLOUD_ACCESS_KEY_ID=your-access-key-id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-access-key-secret
ALIBABA_CLOUD_ACCOUNT_ID=your-main-account-id
ALIBABA_CLOUD_REGION=cn-hangzhou

# Code Interpreter Sandbox 模板名称（必需）
TEMPLATE_NAME=sandbox-your-template-name
```

### 4. 运行示例

```bash
# 运行代码执行示例
python code_exec.py
```

程序会：
1. 创建 Code Interpreter Sandbox
2. 创建执行上下文
3. 执行示例代码（计算圆面积、当前时间）
4. 继续执行代码（复用上下文，计算周长）
5. 销毁 Sandbox

## 核心功能详解

### 1. 创建 Sandbox

```python
from code_exec import create_sandbox

# 创建新的 Code Interpreter Sandbox
sandbox = create_sandbox()
print(f"Sandbox ID: {sandbox.sandbox_id}")
print(f"状态: {sandbox.status}")
```

### 2. 连接到已存在的 Sandbox

```python
from code_exec import connect_sandbox

# 连接到已存在的 Sandbox
sandbox = connect_sandbox(sandbox_id="your-sandbox-id")
```

### 3. 创建执行上下文

```python
from code_exec import create_context

# 创建代码执行上下文
context = create_context(sandbox, language="python", cwd="/home/user")
```

### 4. 执行代码

```python
from code_exec import execute_code

# 在上下文中执行代码
result = execute_code(context, """
import math
radius = 5
area = math.pi * radius ** 2
print(f"圆面积: {area:.2f}")
""")

print(result['results'])
```

**注意**：在同一个上下文中执行代码，变量状态会保持：

```python
# 第一次执行，定义 radius 变量
result = execute_code(context, "radius = 5")

# 第二次执行，可以使用之前定义的变量
result = execute_code(context, "print(f'半径: {radius}')")
```

### 5. 销毁 Sandbox

```python
from code_exec import destroy_sandbox

# 销毁 Sandbox，释放资源
destroy_sandbox(sandbox)
```

## 完整示例

```python
from code_exec import create_sandbox, create_context, execute_code, destroy_sandbox

sandbox = None

try:
    # 创建 Sandbox
    sandbox = create_sandbox()
    
    # 创建执行上下文
    context = create_context(sandbox)
    
    # 执行代码
    result = execute_code(context, """
import math
radius = 5
area = math.pi * radius ** 2
print(f"圆面积: {area:.2f}")
""")
    print(result['results'])
    
    # 继续执行（变量状态保持）
    result = execute_code(context, """
circumference = 2 * math.pi * radius
print(f"周长: {circumference:.2f}")
""")
    print(result['results'])

finally:
    # 销毁 Sandbox
    if sandbox:
        destroy_sandbox(sandbox)
```

## 函数说明

| 函数 | 功能 | 参数 |
|------|------|------|
| `create_sandbox(template_name, idle_timeout)` | 创建 Code Interpreter Sandbox | `template_name`: 模板名称<br>`idle_timeout`: 空闲超时时间（秒） |
| `connect_sandbox(sandbox_id)` | 连接到已存在的 Sandbox | `sandbox_id`: Sandbox ID |
| `create_context(sandbox, language, cwd)` | 创建代码执行上下文 | `sandbox`: Sandbox 实例<br>`language`: 编程语言<br>`cwd`: 工作目录 |
| `execute_code(context, code)` | 在上下文中执行代码 | `context`: 执行上下文<br>`code`: 代码字符串 |
| `destroy_sandbox(sandbox)` | 销毁 Sandbox | `sandbox`: Sandbox 实例 |

## 故障排查

### 环境配置问题

#### 阿里云访问密钥错误

```bash
# 检查环境变量
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(f'AK ID: {os.getenv(\"ALIBABA_CLOUD_ACCESS_KEY_ID\", \"未设置\")[:10]}...')
print(f'Account ID: {os.getenv(\"ALIBABA_CLOUD_ACCOUNT_ID\", \"未设置\")}')
"
```

### Sandbox 创建问题

#### Sandbox 创建失败

```bash
# 检查 agentrun SDK 是否正确安装
pip show agentrun-sdk

# 重新安装
uv pip install --upgrade agentrun-sdk

# 检查模板名称是否正确
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(f'Template Name: {os.getenv(\"TEMPLATE_NAME\", \"未设置\")}')"
```

#### 连接超时

```bash
# 检查网络连接
ping agentrun.cn-hangzhou.aliyuncs.com
```

### 依赖安装问题

```bash
# 删除现有虚拟环境
rm -rf .venv

# 重新创建
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 依赖说明

主要依赖：

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| `agentrun-sdk[playwright,server]` | >= 0.0.8 | AgentRun SDK（包含 Playwright 和 Server 扩展）|
| `python-dotenv` | >= 1.0.0 | 环境变量管理 |

完整依赖列表请查看 `requirements.txt`。

## 参考资源

- [AgentRun SDK 文档](https://github.com/alibaba/agentrun-sdk)
- [AgentRun 文档中心](https://doc.agent.run/)
- [AgentRun 控制台](https://functionai.console.aliyun.com/agent/explore)
