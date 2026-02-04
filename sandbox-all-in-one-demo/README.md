# AgentRun AIO Demo - AI 对话式代码生成与执行平台

基于 **LangChain** 和**阿里云百炼大模型**的 AI 对话式代码生成平台，支持自然语言交互、智能代码生成、Sandbox 执行和实时可视化。

**重大更新（2026-01-29）**：已从 Python + Playwright 迁移到 **Node.js + Puppeteer**，执行更稳定，零依赖问题！

---

## 📋 目录

- [项目概览](docs/OVERVIEW.md) - 了解项目核心价值和架构
- [快速启动](#-快速启动) - 已有环境，立即开始
- [新手指南](docs/QUICKSTART_FOR_BEGINNERS.md) - 完全新手，手把手教程
- [核心功能](#-核心功能)
- [环境准备](#-环境准备)
- [安装部署](#-安装部署)
- [开发指南](#-开发指南)
- [使用示例](#-使用示例)
- [常见问题](#-常见问题)

---

## 🎯 快速启动

如果你已经准备好所有环境变量，可以通过以下命令快速启动：

```bash
# 1. 配置环境变量
cat > .env << 'EOF'
DASHSCOPE_API_KEY=sk-your-dashscope-api-key
AGENTRUN_ACCESS_TOKEN=your-agentrun-token
AIO_TEMPLATE_NAME=your-aio-template
AGENTRUN_ACCOUNT_ID=your-account-id
EOF

# 2. 安装依赖（首次运行）
uv pip install -r requirements.txt

# 3. 启动服务
uv run src/main.py

# 4. 访问应用
# 浏览器打开 http://localhost:8181
```

> 如果你是第一次部署，请继续阅读下面的详细说明。

---

## 核心功能

### AI 对话能力
- **自然语言交互** - 用中文描述需求，AI 自动生成代码
- **多轮对话** - 支持连续对话，AI 能记住上下文
- **智能代码拆分** - 自动将复杂任务拆分为多个步骤，避免超时
- **Node.js + Puppeteer** - 使用 Node.js 生成浏览器自动化代码

### 豆瓣电影分析（内置示例）
- **Cookie 登录** - 自动检测和加载豆瓣 cookies
- **最新电影获取** - 爬取正在上映的最新电影
- **评论爬取** - 批量获取电影短评
- **情感分析** - 中文评论情感分类

### 代码执行
- **Node.js 执行** - 内置 Puppeteer，零依赖安装
- **Sandbox 隔离执行** - 安全的代码执行环境
- **浏览器会话持久化** - disconnect 不关闭浏览器，步骤间保持状态
- **实时日志** - WebSocket 推送执行日志
- **VNC 可视化** - 实时查看浏览器操作过程

### Web 界面
- **左侧：对话面板** - AI 聊天和代码显示
- **中间：VNC 画面** - 实时浏览器操作
- **右侧：日志面板** - 执行进度和输出

---

## 🔧 环境准备

### 系统要求

- **操作系统**: Linux / macOS / Windows（推荐 Linux/macOS）
- **Python**: 3.11 或更高版本
- **Node.js**: 16 或更高版本（前端开发时需要）
- **网络**: 需要访问阿里云百炼 API 和 AgentRun 服务

### 必需的工具

#### 1. Python 环境

检查 Python 版本：
```bash
python --version  # 应输出 Python 3.11.x 或更高
```

如果没有安装 Python 3.11+，请访问 [Python 官网](https://www.python.org/downloads/) 下载安装。

#### 2. Python 包管理器（二选一）

**方法 A: 使用 uv（推荐）**

uv 是一个快速的 Python 包管理器，安装速度比 pip 快很多：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证安装
uv --version
```

**方法 B: 使用 pip（内置）**

Python 自带 pip，无需额外安装：
```bash
pip --version
```

#### 3. 前端工具（仅开发时需要）

如果你需要修改前端代码，需要安装 Node.js 和 pnpm：

```bash
# 1. 安装 Node.js（访问 https://nodejs.org 下载）
node --version  # 应输出 v16.x.x 或更高

# 2. 安装 pnpm
npm install -g pnpm

# 验证安装
pnpm --version
```

> **注意**: 如果只是使用本项目而不修改前端，无需安装 Node.js 和 pnpm。

### 必需的 API 密钥

在开始之前，你需要准备以下 API 密钥：

| 服务 | 用途 | 获取方式 |
|------|------|---------|
| **阿里云百炼** | AI 对话和代码生成 | [获取 API Key](#如何获取阿里云百炼-api-key) |
| **AgentRun** | Sandbox 执行环境 | [获取 Access Token](#如何获取-agentrun-配置) |

#### 如何获取阿里云百炼 API Key

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 创建应用或选择已有应用
4. 在应用详情页找到 **API Key**（格式：`sk-xxx`）
5. 复制保存该 API Key

#### 如何获取 AgentRun 配置

AgentRun 提供云端 Sandbox 执行环境，你需要以下配置项：

- `AGENTRUN_ACCESS_TOKEN`: 访问令牌
- `AIO_TEMPLATE_NAME`: Sandbox 模板名称
- `AGENTRUN_ACCOUNT_ID`: 账户 ID

> **获取方式**: 请参考 [AgentRun 官方文档](https://agentrun.ai) 注册账号并获取配置。

---

## 📦 安装部署

### 第 1 步：克隆项目

```bash
# 克隆代码仓库
git clone <repository-url>
cd agentrun-aio-demo
```

### 第 2 步：配置环境变量

创建 `.env` 文件并填入你的配置：

```bash
# 方式 1: 使用命令行创建
cat > .env << 'EOF'
# 阿里云百炼 API Key（必需）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key

# AgentRun Sandbox 配置（必需）
AGENTRUN_ACCESS_TOKEN=your-agentrun-token
AIO_TEMPLATE_NAME=your-aio-template
AGENTRUN_ACCOUNT_ID=your-account-id
EOF

# 方式 2: 手动创建文件
# 复制 .env.example（如果有）或直接创建 .env 文件
# 然后使用文本编辑器填入上述配置
```

**环境变量说明**：

| 变量名 | 说明 | 示例值 | 必需 |
|--------|------|--------|------|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key | `sk-xxx` | 是 |
| `AGENTRUN_ACCESS_TOKEN` | AgentRun 访问令牌 | `your-token` | 是 |
| `AIO_TEMPLATE_NAME` | Sandbox 模板名称 | `your-template` | 是 |
| `AGENTRUN_ACCOUNT_ID` | AgentRun 账户 ID | `your-account-id` | 是 |

### 第 3 步：安装 Python 依赖

选择以下任一方式安装：

**方式 A: 使用 uv（推荐，速度快）**

```bash
# 直接安装依赖
uv pip install -r requirements.txt
```

**方式 B: 使用 pip（标准方式）**

```bash
# 建议先创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**安装成功标志**：

如果看到类似以下输出，说明安装成功：
```
Successfully installed langchain-x.x.x fastapi-x.x.x ...
```

### 第 4 步：准备豆瓣 Cookies（可选）

如果需要使用豆瓣登录功能（爬取需要登录才能看到的内容），需要配置 cookies：

```bash
# 1. 复制示例文件
cp data/douban_cookies.example.json data/douban_cookies.json

# 2. 编辑文件填入你的 cookies
# 使用任意文本编辑器打开 data/douban_cookies.json
```

**如何获取豆瓣 Cookies**：

1. 使用浏览器访问 https://www.douban.com/ 并登录
2. 按 `F12` 打开开发者工具
3. 切换到 `Application`（应用）标签
4. 左侧选择 `Cookies` → `https://www.douban.com`
5. 找到以下 cookie 并复制其值：
   - `bid`
   - `dbcl2`
   - `ck`
6. 将这些值填入 `data/douban_cookies.json` 文件

**cookies 文件格式**：
```json
[
  {
    "name": "bid",
    "value": "your-bid-value",
    "domain": ".douban.com"
  },
  {
    "name": "dbcl2",
    "value": "your-dbcl2-value",
    "domain": ".douban.com"
  },
  {
    "name": "ck",
    "value": "your-ck-value",
    "domain": ".douban.com"
  }
]
```

> **注意**: 如果只是测试基本功能（如爬取必应等公开网站），可以跳过此步骤。

### 第 5 步：启动后端服务

```bash
# 使用 uv 启动（推荐）
uv run src/main.py

# 或使用 python 启动
python src/main.py
```

**启动成功标志**：

看到以下输出说明服务启动成功：

```
======================================================================
[远程模式] 默认模式
将使用 AgentRun SDK 调用远程云服务
注意：远程模式有 30 秒执行限制
======================================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8181 (Press CTRL+C to quit)
```

### 第 6 步：访问应用

打开浏览器，访问：

```
http://localhost:8181
```

你应该能看到如下界面：
- **左侧**: 对话面板（可输入聊天消息）
- **中间**: VNC 画面（实时浏览器操作）
- **右侧**: 日志面板（执行日志）

**首次使用**：
1. 点击顶部的 "创建 Sandbox" 按钮
2. 等待 Sandbox 创建完成（约 30 秒）
3. 在左侧聊天框输入你的需求，例如："打开必应搜索"
4. AI 会生成代码，点击 "运行" 按钮执行

---

## 💻 开发指南

### 前端开发模式

如果你需要修改前端代码（React + TypeScript），请按以下步骤操作。

#### 1. 安装前端依赖

```bash
cd frontend
pnpm install
```

#### 2. 启动前端开发服务器

```bash
# 在 frontend 目录下执行
pnpm run dev
```

前端开发服务器会启动在 `http://localhost:5173`，并自动代理 API 请求到后端 `http://localhost:8181`。

#### 3. 前后端联调

**需要开启两个终端**：

```bash
# 终端 1: 启动后端（端口 8181）
cd /path/to/agentrun-aio-demo
uv run src/main.py

# 终端 2: 启动前端开发服务器（端口 5173）
cd /path/to/agentrun-aio-demo/frontend
pnpm run dev
```

然后访问 `http://localhost:5173` 进行开发，修改代码后会自动热重载。

#### 4. 构建前端

开发完成后，构建前端产物：

```bash
cd frontend
pnpm run build
```

构建产物会输出到 `frontend/dist/` 目录，后端会自动使用最新的构建产物。

### 部署模式对比

#### 模式 1: 开发模式（前后端分离）

**适用场景**: 开发和调试前端时使用

```bash
# 终端 1: 后端（端口 8181）
uv run src/main.py

# 终端 2: 前端开发服务器（端口 5173）
cd frontend && pnpm run dev
```

- **访问地址**: `http://localhost:5173`
- **优点**: 支持热重载，开发效率高
- **缺点**: 需要两个终端，资源占用稍多

#### 模式 2: 生产模式（一体化）

**适用场景**: 生产部署或只使用不开发前端

```bash
# 1. 构建前端（首次或修改后执行一次）
cd frontend && pnpm run build && cd ..

# 2. 启动后端（包含静态文件服务）
uv run src/main.py
```

- **访问地址**: `http://localhost:8181`
- **优点**: 单进程，部署简单
- **缺点**: 修改前端需重新构建

> **推荐**: 如果只是使用本项目，直接使用模式 2 即可。前端已预先构建好，无需额外操作。

### 项目结构说明

```
agentrun-aio-demo/
├── src/                       # 后端源码（Python）
│   ├── main.py               # FastAPI 主服务（端口 8181）
│   ├── ai_code_generator.py  # AI 代码生成器（LangChain）
│   └── sandbox_executor.py   # Sandbox 执行器
│
├── frontend/                 # 前端项目（React + TypeScript）
│   ├── src/                  # 前端源码
│   │   ├── components/       # React 组件
│   │   │   ├── chat/        # 对话相关组件
│   │   │   ├── playground/  # Playground 组件（编辑器、VNC、日志）
│   │   │   └── layout/      # 布局组件
│   │   ├── stores/          # Zustand 状态管理
│   │   ├── lib/api/         # API 客户端
│   │   └── pages/           # 页面组件
│   ├── dist/                # 前端构建产物（已预构建）
│   ├── package.json         # 前端依赖配置
│   └── vite.config.ts       # Vite 构建配置
│
├── data/                     # 数据文件目录
│   ├── douban_cookies.json  # 豆瓣 cookies（可选）
│   └── *.json              # 爬取结果文件
│
├── docs/                    # 项目文档
│   ├── CHAT_USAGE_GUIDE.md  # 对话功能使用指南
│   ├── AI_CHAT_SYSTEM_DESIGN.md  # 系统设计文档
│   └── 2026-02-04-CODE-REVIEW-*.md  # Code Review 报告
│
├── scripts/                # 工具脚本
│   └── remove_emojis.py    # Emoji 移除脚本
│
├── .env                     # 环境变量配置（需手动创建）
├── requirements.txt         # Python 依赖清单
├── pyproject.toml          # Python 项目配置
└── README.md               # 项目说明文档（本文件）
```

**核心文件说明**：

| 文件/目录 | 说明 | 是否需要修改 |
|----------|------|-------------|
| `src/main.py` | 后端主服务入口 | 较少修改 |
| `src/ai_code_generator.py` | AI 代码生成逻辑，可自定义 Prompt | 需要调整 AI 行为时修改 |
| `frontend/src/` | 前端源码 | 需要修改 UI 时编辑 |
| `frontend/dist/` | 前端构建产物 | 自动生成，勿手动修改 |
| `.env` | 环境变量配置 | 首次部署必须创建 |
| `data/douban_cookies.json` | 豆瓣登录凭证 | 需要豆瓣登录时配置 |

### 自定义 AI 行为

如果你想调整 AI 生成代码的行为（例如修改提示词、生成不同语言的代码），可以编辑 `src/ai_code_generator.py`：

```python
# 文件位置: src/ai_code_generator.py

def _build_system_prompt(self) -> str:
    """构建系统提示词"""
    return """
    你是一个专业的代码生成助手。
    
    # 在这里修改提示词
    # 例如：添加新的规则、调整代码风格等
    
    ... 现有提示词内容 ...
    """
```

修改后重启后端服务即可生效。

---

## 📖 使用示例

### 示例 1: 简单的网页访问（入门）

这是一个最简单的示例，适合第一次使用本系统。

**步骤 1: 输入需求**

在左侧聊天框输入：

```
打开必应搜索，获取页面标题
```

**步骤 2: AI 生成代码**

AI 会自动生成 Node.js 代码：

```javascript
const puppeteer = require('puppeteer-core');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        const page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });
        
        console.log('🌐 正在打开必应...');
        await page.goto('https://www.bing.com', { waitUntil: 'networkidle2' });
        
        const title = await page.title();
        console.log('✅ 页面标题:', title);
        
    } finally {
        if (browser) await browser.disconnect();
    }
}

main().catch(err => console.error('错误:', err));
```

**步骤 3: 执行代码**

点击代码下方的 **▶️ 运行** 按钮。

**步骤 4: 查看结果**

- **中间 VNC 画面**: 可以看到浏览器打开必应页面
- **右侧日志面板**: 显示执行日志
  ```
  🌐 正在打开必应...
  ✅ 页面标题: 必应
  ```

### 示例 2: 豆瓣电影评论分析（完整流程）

这是一个完整的爬虫示例，展示了如何使用多步骤完成复杂任务。

**步骤 1: 输入需求**

```
打开豆瓣电影，在我完成登录之后，获取最新三个电影的评论并进行情感分析
```

**步骤 2: AI 生成多个步骤**

AI 会自动将任务拆分为多个步骤：
- **步骤 1**: 连接浏览器并打开豆瓣电影（等待用户登录）
- **步骤 2**: 登录后获取最新上映的电影列表
- **步骤 3**: 爬取电影评论
- **步骤 4**: 保存和分析结果

**步骤 3: 执行第一步（打开页面）**

```javascript
const puppeteer = require('puppeteer-core');

async function step1() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('✅ 浏览器连接成功');
        const page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });
        
        console.log('🌐 正在打开豆瓣电影...');
        await page.goto('https://movie.douban.com/', { waitUntil: 'networkidle2' });
        
        console.log('✅ 页面已打开，请在 VNC 界面完成登录');
        console.log('⏸️  完成登录后，请执行步骤 2');
        
    } catch (error) {
        console.error('❌ 错误:', error.message);
    } finally {
        if (browser) await browser.disconnect();  // 注意：使用 disconnect() 保持浏览器状态
    }
}

step1().catch(err => console.error('💥 错误:', err));
```

点击 **▶️ 运行**，然后在 VNC 画面中手动完成登录。

**步骤 4: 执行后续步骤**

登录完成后，依次点击后续步骤的 **▶️ 运行** 按钮。

**步骤 5: 查看结果**

- **右侧日志面板**:
  ```
  🎬 正在获取最新上映电影...
  1. 电影A
  2. 电影B
  3. 电影C
  
  《电影A》评论分析：
    📈 总评论数：10
    😊 积极评论：7 (70.0%)
    😞 消极评论：2 (20.0%)
    😐 中性评论：1 (10.0%)
  ```

- **结果文件**: 保存在 Sandbox 的 `/home/user/movie_comments_analysis.json`

### 示例 3: 其他爬虫任务

**微博热搜**:
```
帮我爬取微博热搜 Top 10
```

**知乎问题**:
```
帮我爬取知乎"人工智能"话题下的高赞回答
```

**GitHub 趋势**:
```
爬取 GitHub Trending 今日最热门的项目
```

### 多步骤任务的关键点

1. **使用 `disconnect()` 而不是 `close()`**
   - `disconnect()`: 断开连接但保持浏览器状态（推荐用于多步骤任务）
   - `close()`: 完全关闭浏览器（只在任务结束时使用）

2. **保持浏览器会话**
   ```javascript
   // 步骤 1: 打开页面
   await browser.disconnect(); // 保持浏览器打开
   
   // 步骤 2: 重新连接
   browser = await puppeteer.connect({ browserWSEndpoint }); // 恢复之前的会话
   ```

3. **任务拆分原则**
   - 每个步骤执行时间 < 30 秒
   - 需要手动操作的地方单独一步
   - 耗时操作（如大量爬取）分多步执行

---

---

## 📚 详细文档

### 入门指南

- **[项目概览](docs/OVERVIEW.md)** - 快速了解项目核心价值和技术架构
- **[新手快速开始指南](docs/QUICKSTART_FOR_BEGINNERS.md)** - 面向完全新手的手把手教程
- **[部署检查清单](docs/DEPLOYMENT_CHECKLIST.md)** - 确认所有部署步骤已完成

### 技术文档

- **[系统设计文档](docs/AI_CHAT_SYSTEM_DESIGN.md)** - 完整的架构设计和实现细节
- **[All-in-One Sandbox 最佳实践](docs/all-in-one-sandbox-best-practices-v4.md)** - Sandbox 使用指南

### 开发相关

- **[Code Review 报告](docs/2026-02-04-CODE-REVIEW-opensource-preparation.md)** - 开源准备检查详情
- **[Code Review 总结](docs/2026-02-04-CODE-REVIEW-SUMMARY.md)** - 审查进度和建议

### 更新日志

- **[迁移到 Node.js + Puppeteer](docs/2026-01-29T10:00:00-CHANGE-LOG-migrate-to-nodejs-puppeteer.md)** - 重要架构升级
- **[本地模式支持](docs/2026-01-29T17:00:00-CHANGE-LOG-add-local-mode-support.md)** - 绕过 30 秒限制
- **[完整 Change Log](docs/)** - 查看所有更新历史

---

## 🔧 技术栈

### 后端
- **LangChain** - AI 对话框架
- **langchain-openai** - OpenAI 兼容接口（阿里云百炼）
- **FastAPI** - Web 服务框架
- **Uvicorn** - ASGI 服务器
- **AgentRun SDK** - Sandbox 管理
- **Python 3.11+** - 后端服务和数据处理

### 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Zustand** - 状态管理
- **TailwindCSS** - 样式框架
- **shadcn/ui** - UI 组件库
- **noVNC** - VNC 客户端

### 代码执行
- **Node.js (主要)** - 浏览器自动化，内置 Puppeteer
- **Python (可选)** - 数据处理和分析
- **Shell 命令** - 依赖安装等

---

## 📊 API 接口

### 对话相关

- `POST /api/chat/send` - 发送消息，AI 生成代码
- `POST /api/chat/execute` - 执行代码
- `GET /api/chat/history/{session_id}` - 获取对话历史
- `WebSocket /ws/chat/{session_id}` - 实时消息推送

### Sandbox 管理

- `POST /api/sandbox/create` - 创建 Sandbox
- `GET /api/sandboxes` - 获取所有 Sandbox
- `GET /api/sandboxes/{sandbox_id}` - 获取 Sandbox 信息
- `DELETE /api/sandbox/{sandbox_id}` - 删除 Sandbox

### 日志推送

- `POST /api/log/{sandbox_id}` - 推送日志
- `WebSocket /ws/log/{sandbox_id}` - 实时日志流

---

## 注意事项

### 安全与隐私

1. **API Key 安全**
   - 不要将 `.env` 文件提交到 Git 仓库（已在 `.gitignore` 中配置）
   - 不要在代码中硬编码任何 API Key 或 Token
   
2. **敏感数据保护**
   - `data/` 目录下的所有 `.json` 文件会被 Git 忽略
   - **警告**：不要将包含真实用户信息的 cookies 文件提交到仓库
   - 建议使用 `data/*.example.json` 文件作为模板，不包含真实数据

3. **Cookie 管理最佳实践**
   ```bash
   # 正确做法：复制示例文件，填入自己的 cookies
   cp data/douban_cookies.example.json data/douban_cookies.json
   # 然后编辑 data/douban_cookies.json（此文件已被 Git 忽略）
   ```

### 使用规范

4. **爬虫规范**: 请遵守目标网站的使用条款和 robots.txt

5. **Sandbox 成本**: AgentRun Sandbox 按使用量计费，记得及时清理不用的 Sandbox

6. **反爬虫机制**: 豆瓣等网站有反爬虫机制，建议：
   - 使用 cookies 登录
   - 设置合理的请求延迟
   - 限制单次爬取数量
   - 在 VNC 中手动操作更可靠

7. **执行时间限制**: 单次代码执行限制为 30 秒，复杂任务请拆分为多步骤

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 提交代码前的检查

在提交 Pull Request 之前，请确保：

1. **代码规范**
   - 不要在代码、注释、日志中使用 emoji
   - 使用清晰的文本标记，如 `[OK]`、`[ERROR]`、`[WARNING]` 等
   - Python 代码遵循 PEP 8 规范
   - TypeScript/React 代码遵循项目的 ESLint 配置

2. **安全检查**
   - 不要提交 `.env` 文件
   - 不要提交包含真实用户数据的文件（cookies、个人信息等）
   - 不要硬编码任何 API Key、Token 或密码
   - 运行 `git status` 确认没有敏感文件被追踪

3. **代码质量**
   - 添加必要的注释说明复杂逻辑
   - 确保代码可以正常运行
   - 如果修改了核心功能，请更新相关文档

### 如何贡献

1. **报告问题**
   - 提交 Issue 描述问题或建议
   - 包含复现步骤、预期行为、实际行为
   - 附上相关日志或截图

2. **贡献代码**
   - Fork 项目并创建新分支
   - 在分支上进行开发
   - 提交 Pull Request，描述修改内容和原因

3. **改进文档**
   - 发现文档错误或不清晰的地方
   - 提交 Pull Request 改进文档

### 工具脚本

项目提供了一些辅助工具：

```bash
# 移除代码中的 emoji（开源准备）
python scripts/remove_emojis.py
```