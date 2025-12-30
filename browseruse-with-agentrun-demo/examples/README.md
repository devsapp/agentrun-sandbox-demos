# 示例代码使用说明

## 抽象接口设计理念

所有示例代码（01-02）都使用 `common.py` 提供的抽象接口，**用户无需感知底层的 VNC Server 实现细节**，避免平台特殊差异暴露在示例代码中。

### 设计原则

1. **完全抽象** - 示例代码不直接依赖 `vncviewer` 模块
2. **优雅降级** - VNC Server 不可用时，自动降级到标准输出
3. **简洁易用** - 提供统一的、简洁的 API
4. **无侵入性** - 不影响业务逻辑，静默失败

## 核心接口

### 1. Logger 接口 (`create_logger()`)

```python
from common import create_logger

# 创建 logger
logger = create_logger(session_id="your_session_id")

# 只提供 4 个基础日志方法
logger.info("ℹ普通信息")
logger.debug("调试信息")
logger.warning("警告信息")
logger.error("错误信息")

# 示例代码使用基础方法构造业务日志
logger.info("步骤 1: 创建资源")
logger.info("AI 正在分析...")

# 关闭 logger（可选）
logger.close()
```

**设计理念：**
- **简洁** - 只提供基础方法（info, debug, warning, error）
- **灵活** - 示例代码自行构造日志内容和格式
- **标准** - 使用标准的日志方法，易于理解
- **降级** - VNC Server 不可用时自动降级（静默失败）

**推荐的日志格式：**
- 步骤日志：`logger.info("步骤 1: 描述")`
- 思考日志：`logger.info("AI 正在分析...")`
- 操作日志：`logger.info("执行操作: 描述")`
- 成功日志：`logger.info("操作成功")`
- 错误日志：`logger.error("操作失败: 原因")`
- 警告日志：`logger.warning("警告信息")`

### 2. 打印工具函数

#### `print_section()` - 打印分隔线标题

```python
from common import print_section

print_section("步骤 1: 创建 Sandbox")
# 输出：
# ============================================================
# 步骤 1: 创建 Sandbox
# ============================================================
```

#### `print_info()` - 打印键值对信息

```python
from common import print_info

print_info("Sandbox ID", "sandbox-123")
print_info("CDP URL", "wss://...")
# 输出：
#    Sandbox ID: sandbox-123
#    CDP URL: wss://...
```

#### `print_result()` - 打印结果（带边框）

```python
from common import print_result

print_result("任务执行成功\n结果：...")
# 输出：
# ------------------------------------------------------------
# 任务执行成功
# 结果：...
# ------------------------------------------------------------
```

#### `print_execution_stats()` - 打印执行统计

```python
from common import print_execution_stats

result = await agent.run()
print_execution_stats(
    result,
    show_tokens=True,      # 显示 Token 使用情况
    show_thoughts=True,    # 显示思考过程
    max_thoughts=3         # 最多显示 3 条思考记录
)
```

### 3. 配置验证

```python
from common import validate_settings
from config import get_settings

settings = get_settings()
if not validate_settings(settings):
    print("配置不完整，请检查 .env 文件")
    return
```

### 4. 环境设置

```python
from common import setup_example_environment

# 自动加载 .env 文件，设置日志级别等
setup_example_environment()
```

## 使用方式

### 方式 1：不使用 VNC Server（传统方式）

只需配置 `.env` 文件：

```bash
# .env 文件
CDP_URL=wss://your-cdp-url...
DASHSCOPE_API_KEY=sk-your-key
```

运行示例：

```bash
python examples/01_browseruse_basic.py
```

### 方式 2：使用 VNC Server（推荐）

**步骤 1：启动 VNC Server**

```bash
python main.py
```

**步骤 2：运行示例**

```bash
python examples/01_browseruse_basic.py
```

**效果：**
- 浏览器自动打开前端界面
- 左侧实时显示日志
- 右侧实时显示 VNC 画面
- 无需修改示例代码

## Sandbox 自动清理机制

### 概述

项目实现了**三层清理机制**，确保无论程序如何退出，Sandbox 资源都能被正确释放：

1. **显式清理** - `finally` 块中的 `destroy_sandbox()`
2. **信号处理** - 捕获 Ctrl+C (SIGINT) 和 kill (SIGTERM)
3. **atexit 兜底** - 程序退出时自动清理

### 清理场景

程序正常退出 - 自动清理  
Ctrl+C 中断 - 自动清理  
程序异常退出 - 自动清理  
kill 命令终止 - 自动清理  
kill -9 强制终止 - 无法清理（建议设置 idle_timeout）

### 使用方式

**方式 1: 依赖自动清理（推荐）**

```python
from runner import create_or_get_sandbox

# 创建 Sandbox
sandbox = create_or_get_sandbox(
    user_id="user123",
    session_id="session456",
    thread_id="thread789",
    idle_timeout=600  # 10 分钟超时
)

# 使用 Sandbox
# ... 执行任务 ...

# 程序退出时会自动清理，无需手动调用
```

**方式 2: 显式清理 + 自动清理（双重保障）**

```python
from runner import create_or_get_sandbox, destroy_sandbox

sandbox = None

try:
    sandbox = create_or_get_sandbox(...)
    # 使用 Sandbox
finally:
    # 显式清理（优先）
    if sandbox:
        destroy_sandbox(sandbox['sandbox_id'])
    # atexit 会作为兜底
```

**方式 3: 上下文管理器**

```python
from sandbox_manager import SandboxManager

with SandboxManager() as manager:
    sandbox_info = manager.create()
    # 使用 sandbox
# 自动清理
```

### 测试清理逻辑

```bash
# 测试正常退出
python examples/test_cleanup.py normal

# 测试 Ctrl+C 中断
python examples/test_cleanup.py interrupt

# 测试异常退出
python examples/test_cleanup.py error

# 测试手动中断
python examples/test_cleanup.py delay

# 测试多个 Sandbox
python examples/test_cleanup.py multiple
```

### 相关文档

- [Sandbox 清理机制使用指南](../docs/SANDBOX_CLEANUP_GUIDE.md) - 完整的使用说明
- [清理机制实现总结](../docs/CLEANUP_IMPLEMENTATION_SUMMARY.md) - 技术实现细节

## 环境变量配置

### 基础配置（必需）

```bash
# DashScope API Key
DASHSCOPE_API_KEY=sk-your-key

# CDP URL（如果不使用 VNC Server）
CDP_URL=wss://your-cdp-url...
```

### VNC Server 配置（可选）

```bash
# 启用 VNC Server（默认：true）
ENABLE_VNC_SERVER=true

# VNC Server 地址（默认：http://localhost:8080）
VNC_SERVER_URL=http://localhost:8080

# Session ID（自动生成，也可手动指定）
VNC_SESSION_ID=20240101_120000_abc12345
```

## 示例代码模板

### 最简单的使用方式

```python
"""
最简单的 BrowserUse 示例 - 使用 common 模块
"""

import asyncio
from browser_use import Agent, BrowserSession, ChatOpenAI
from browser_use.browser import BrowserProfile
from config import get_settings
from runner import create_or_get_sandbox, set_vnc_url, get_vnc_viewer_url, destroy_sandbox

# 导入统一的 common 模块
from common import (
    create_logger,
    setup_example_environment,
    validate_settings,
    print_section,
    print_result,
    print_execution_stats,
    get_env_or_default
)

# 设置示例环境
setup_example_environment()

async def main():
    """主函数"""
    settings = get_settings()
    
    print_section("我的示例")
    
    # 1. 验证配置
    if not validate_settings(settings):
        return
    
    # 2. 创建 Sandbox
    sandbox = create_or_get_sandbox(
        user_id=get_env_or_default("USER_ID", "my_user"),
        session_id=get_env_or_default("SESSION_ID", "my_session"),
        thread_id=get_env_or_default("THREAD_ID", "my_thread")
    )
    
    # 3. 创建 logger
    logger = create_logger(session_id=sandbox['sandbox_id'])
    logger.info("示例开始执行")
    
    # 4. 设置 VNC（可选）
    if sandbox.get('vnc_url'):
        set_vnc_url(sandbox['sandbox_id'], sandbox['vnc_url'])
        viewer_url = get_vnc_viewer_url(sandbox['sandbox_id'])
        logger.info(f"VNC Viewer: {viewer_url}")
    
    try:
        # 5. 创建浏览器会话
        logger.step("创建浏览器会话")
        browser_session = BrowserSession(
            cdp_url=sandbox['cdp_url'],
            browser_profile=BrowserProfile(
                headless=settings.browser_headless,
                keep_alive=True,
            )
        )
        
        # 6. 配置 LLM
        logger.step("配置 LLM")
        llm = ChatOpenAI(
            model=settings.qwen_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        
        # 7. 创建 Agent 并执行任务
        logger.step("创建 Agent")
        agent = Agent(
            task="你的任务描述",
            llm=llm,
            browser_session=browser_session,
            use_vision=settings.browser_use_vision
        )
        
        logger.step("开始执行任务")
        result = await agent.run()
        
        # 8. 输出结果
        print_section("任务执行结果")
        final_result = result.final_result()
        print_result(final_result)
        
        logger.result("任务执行完成", steps=len(result.model_thoughts()))
        
        # 9. 显示统计信息
        print_execution_stats(result, show_tokens=True, show_thoughts=True)
        
        # 10. 清理资源
        logger.step("清理资源")
        await browser_session.stop()
        
        logger.info("✨ 示例执行完成")
        
    finally:
        # 销毁 Sandbox
        destroy_sandbox(sandbox['sandbox_id'])

if __name__ == "__main__":
    asyncio.run(main())
```

## 集成到自己的项目

### 方法 1：直接使用 common 模块

将你的脚本放在 `examples/` 目录下，直接导入 `common`：

```python
from common import create_logger, validate_settings, print_section

logger = create_logger("my_session")
logger.info("Hello World")
```

### 方法 2：复制 common.py

将 `examples/common.py` 复制到你的项目中：

```bash
cp examples/common.py your_project/
```

然后在你的代码中使用：

```python
from common import (
    create_logger,
    setup_example_environment,
    validate_settings,
    print_section,
    print_info,
    print_result
)

# 设置环境
setup_example_environment()

# 创建 logger
logger = create_logger(session_id="your_session")

# 使用工具函数
print_section("开始执行任务")
logger.info("任务开始")
logger.step("步骤 1")
logger.result("完成")
```

## 优势

### 完全抽象

- 示例代码不直接导入 `vncviewer` 模块
- 避免平台特殊差异暴露在示例代码中
- 统一的接口，易于理解和使用

### 优雅降级

- VNC Server 不可用时，自动降级
- 不影响业务逻辑，静默失败
- 开发和生产环境无缝切换

### 简洁易用

- 提供高级封装的工具函数
- 减少重复代码
- 提高代码可读性

### 易于维护

- 底层实现变更不影响示例代码
- 集中管理公共逻辑
- 降低维护成本

## 常见问题

### Q1: 为什么要创建 common.py？

**A:** 为了避免在示例代码中直接暴露平台特殊差异的依赖（如 `vncviewer`），提供统一的、简洁的抽象接口。这样：
- 示例代码更简洁、易读
- 底层实现变更不影响示例
- 用户可以无缝在不同环境运行

### Q2: VNC Server 不可用时会怎样？

**A:** 完全不影响：
- `create_logger()` 会静默降级，不抛出异常
- 日志方法调用仍然可以正常执行，只是不会推送到前端
- 业务逻辑正常进行

### Q3: 如何检查 VNC Logger 是否可用？

**A:** 使用 `is_vnc_available()` 方法：

```python
logger = create_logger("session_id")
if logger.is_vnc_available():
    print("VNC Logger 可用")
else:
    print("VNC Logger 不可用，使用标准输出")
```

### Q4: 如何自定义 VNC Server 地址？

**A:** 在创建 logger 时指定：

```python
logger = create_logger(
    session_id="my_session",
    server_url="http://your-vnc-server:8080"
)
```

### Q5: common.py 可以在其他项目中使用吗？

**A:** 可以！`common.py` 是一个独立的模块，可以：
1. 直接复制到你的项目中
2. 根据需要调整配置
3. 扩展或修改功能

只需确保你的项目中有 `vncviewer` 模块（如果需要 VNC 功能）。

## 示例文件说明

| 文件 | 说明 |
|-----|------|
| `01_browseruse_basic.py` | 基础示例：单任务执行 |
| `02_browseruse_advanced.py` | 高级示例：多任务执行、Sandbox 复用 |

所有使用 `common.py` 的示例都不直接导入 `vncviewer` 模块，实现了完全抽象。