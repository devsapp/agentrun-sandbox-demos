"""
Sandbox 代码执行模块

负责 AgentRun Code Interpreter Sandbox 的创建、管理和代码执行。
"""

import os
from dotenv import load_dotenv
from agentrun.sandbox import Sandbox, TemplateType

# 加载环境变量
load_dotenv()


def create_sandbox(template_name: str | None = None, idle_timeout: int = 3000) -> Sandbox:
    """
    创建代码解释器 sandbox

    Args:
        template_name: Sandbox 模板名称，默认从环境变量读取
        idle_timeout: 空闲超时时间（秒），默认 3000 秒

    Returns:
        Sandbox 实例
    """
    if template_name is None:
        template_name = os.getenv("TEMPLATE_NAME", "sandbox-code-interpreter")

    sandbox = Sandbox.create(
        template_type=TemplateType.CODE_INTERPRETER,
        template_name=template_name,
        sandbox_idle_timeout_seconds=idle_timeout
    )

    return sandbox


def connect_sandbox(sandbox_id: str) -> Sandbox:
    """
    连接到已存在的代码解释器 sandbox

    Args:
        sandbox_id: 已存在的 sandbox ID

    Returns:
        Sandbox 实例
    """
    sandbox = Sandbox.connect(
        sandbox_id=sandbox_id,
        template_type=TemplateType.CODE_INTERPRETER
    )

    return sandbox


def create_context(sandbox: Sandbox, language: str = "python", cwd: str = "/home/user"):
    """
    在 sandbox 中创建代码执行上下文

    Args:
        sandbox: Sandbox 实例
        language: 编程语言，默认 python
        cwd: 工作目录

    Returns:
        代码执行上下文对象
    """
    context = sandbox.context.create(
        language=language,
        cwd=cwd
    )
    return context


def execute_code(context, code: str) -> dict:
    """
    在上下文中执行代码

    Args:
        context: 代码执行上下文（由 create_context 创建）
        code: 要执行的代码字符串

    Returns:
        执行结果字典，包含 stdout、stderr、results 等
    """
    result = context.execute(code)
    return result


def stop_sandbox(sandbox: Sandbox) -> None:
    """
    停止 sandbox

    Args:
        sandbox: Sandbox 实例
    """
    sandbox.stop()


# ============ 使用示例 ============

if __name__ == "__main__":
    sandbox = None

    try:
        # 创建 Sandbox
        print("创建 Sandbox...")
        sandbox = create_sandbox()
        print(f"Sandbox 创建成功！")
        print(f"   - Sandbox ID: {sandbox.sandbox_id}")
        print(f"   - 状态: {sandbox.status}")
        print()

        # 创建执行上下文
        print("创建执行上下文...")
        context = create_context(sandbox)
        print("上下文创建成功！")
        print()

        # 执行代码
        print("执行代码...")
        result = execute_code(context, """
import math
import datetime

# 计算圆的面积
radius = 5
area = math.pi * radius ** 2

# 获取当前时间
current_time = datetime.datetime.now()

print(f"半径为 {radius} 的圆面积: {area:.2f}")
print(f"当前时间: {current_time}")
""")
        print("执行结果:")
        print(result['results'])
        print()

        # 继续执行代码（复用同一上下文，变量会保留）
        print("继续执行代码（复用上下文）...")
        result = execute_code(context, """
# 使用之前定义的 radius 变量
circumference = 2 * math.pi * radius
print(f"周长: {circumference:.2f}")
""")
        print("执行结果:")
        print(result['results'])

    finally:
        # 销毁 Sandbox
        if sandbox:
            stop_sandbox(sandbox)
            print(f"\nSandbox 已停止: {sandbox.sandbox_id}")
