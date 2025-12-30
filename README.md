# AgentRun Sandbox Demos

![Browser with Browser Sandbox Preview](browseruse-with-agentrun-demo/docs/preview.png)

This repository contains two comprehensive demo projects showcasing how to use AgentRun Browser Sandbox with different technologies for AI-powered web automation.

[中文版 README](README_CN.md) | [English README](README.md)


## 📁 Projects

### 1. BrowserUse Demo (`browseruse-with-agentrun-demo`)

A complete example of integrating AgentRun Browser Sandbox with BrowserUse and Qwen models, featuring:

- **Session State Management** - Multi-instance isolation and reuse based on user_id/session_id/thread_id
- **VNC Real-time Visualization** - Live browser operation viewing and log streaming
- **Automatic Reuse Mechanism** - Intelligent sandbox reuse to reduce costs
- **Complete Example Code** - From basic to advanced examples
- **Clear Architecture** - Separation of concerns for maintainability and extensibility
- **Automatic Resource Cleanup** - Automatic sandbox resource cleanup on program exit

### 2. LangChain Demo (`langchain-with-agentrun-demo`)

A complete example of using LangChain to manually create Browser Sandbox tools with VNC visualization:

- **Pure LangChain Implementation** - Manual creation of sandbox tools
- **OpenAI Compatible API Support** - Works with DashScope
- **Complete Sandbox Lifecycle Management** - Create, manage, and destroy sandboxes
- **VNC Visualization Integration** - Real-time browser operation viewing
- **Modular Design** - Cohesive, well-organized code structure
- **Automatic Resource Cleanup** - Supports Ctrl+C interruption

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (Python 3.12 recommended)
- uv package manager (recommended) or pip
- Alibaba Cloud account with valid access keys
- DashScope API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd agentrun-sandbox-demos
   ```

2. **Install uv (recommended) or use pip:**
   ```bash
   # Install uv (macOS/Linux)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Navigate to desired demo and install dependencies:**
   ```bash
   # For BrowserUse demo
   cd browseruse-with-agentrun-demo

   # For LangChain demo
   cd langchain-with-agentrun-demo

   # Create virtual environment
   uv venv .venv --python 3.12
   source .venv/bin/activate

   # Install dependencies
   uv pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

5. **Run the demo:**
   - For BrowserUse demo: Follow instructions in `browseruse-with-agentrun-demo/README.md`
   - For LangChain demo: Follow instructions in `langchain-with-agentrun-demo/README.md`

## 🛠️ Technologies Used

- **AgentRun SDK** - Cloud-based browser sandbox management
- **BrowserUse** - Browser automation for AI agents (BrowserUse demo)
- **LangChain** - LLM application framework (LangChain demo)
- **Qwen Models** - Alibaba's large language models via DashScope
- **VNC** - Real-time visualization of browser operations
- **Playwright** - Browser automation library

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
