# AgentRun 沙箱演示

![Browser with Browser Sandbox Preview](browseruse-with-agentrun-demo/docs/preview.png)

本仓库包含两个综合演示项目，展示了如何使用 AgentRun 浏览器沙箱与不同技术结合，实现 AI 驱动的网页自动化。

## 📁 项目

### 1. BrowserUse 演示 (`browseruse-with-agentrun-demo`)

将 AgentRun 浏览器沙箱与 BrowserUse 和 Qwen 模型集成的完整示例，具有以下特性：

- **会话状态管理** - 基于 user_id/session_id/thread_id 的多实例隔离和复用
- **VNC 实时可视化** - 浏览器操作实时查看和日志流
- **自动复用机制** - 智能沙箱复用以降低成本
- **完整示例代码** - 从基础到高级的示例
- **清晰架构** - 职责分离，便于维护和扩展
- **自动资源清理** - 程序退出时自动清理沙箱资源

### 2. LangChain 演示 (`langchain-with-agentrun-demo`)

使用 LangChain 手动创建带有 VNC 可视化的浏览器沙箱工具的完整示例：

- **纯 LangChain 实现** - 手动创建沙箱工具
- **OpenAI 兼容 API 支持** - 支持 DashScope
- **完整的沙箱生命周期管理** - 创建、管理和销毁沙箱
- **VNC 可视化集成** - 浏览器操作实时查看
- **模块化设计** - 内聚且组织良好的代码结构
- **自动资源清理** - 支持 Ctrl+C 中断

## 🚀 快速开始

### 先决条件

- Python 3.10+ (推荐 Python 3.12)
- uv 包管理器 (推荐) 或 pip
- 阿里云账户和有效的访问密钥
- DashScope API 密钥

### 安装

1. **克隆仓库:**
   ```bash
   git clone <repository-url>
   cd agentrun-sandbox-demos
   ```

2. **安装 uv (推荐) 或使用 pip:**
   ```bash
   # 安装 uv (macOS/Linux)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **导航到所需演示并安装依赖:**
   ```bash
   # BrowserUse 演示
   cd browseruse-with-agentrun-demo

   # LangChain 演示
   cd langchain-with-agentrun-demo

   # 创建虚拟环境
   uv venv .venv --python 3.12
   source .venv/bin/activate

   # 安装依赖
   uv pip install -r requirements.txt
   ```

4. **配置环境变量:**
   ```bash
   cp env.example .env
   # 编辑 .env 文件并填入您的凭据
   ```

5. **运行演示:**
   - BrowserUse 演示：请参考 `browseruse-with-agentrun-demo/README.md` 中的说明
   - LangChain 演示：请参考 `langchain-with-agentrun-demo/README.md` 中的说明

## 🛠️ 使用的技术

- **AgentRun SDK** - 基于云的浏览器沙箱管理
- **BrowserUse** - AI 代理的浏览器自动化 (BrowserUse 演示)
- **LangChain** - LLM 应用框架 (LangChain 演示)
- **Qwen 模型** - 阿里巴巴的大语言模型，通过 DashScope 提供
- **VNC** - 浏览器操作实时可视化
- **Playwright** - 浏览器自动化库

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件了解详细信息。

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。