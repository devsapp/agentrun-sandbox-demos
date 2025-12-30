"""
示例 2: BrowserUse 高级示例（多任务执行）

展示如何：
1. 执行单个任务
2. 顺序执行多个任务（复用 Sandbox）
3. 查看详细的执行结果

运行方式：
    python examples/02_browseruse_advanced.py

相比示例 1 的改进：
    ✅ 多任务顺序执行
    ✅ Sandbox 复用
    ✅ 详细的结果输出
"""

import asyncio

# 首先导入 common 模块（会自动设置 sys.path）
from common import (
    create_logger,
    setup_example_environment,
    validate_settings,
    print_section,
    print_info,
    print_result,
    print_vnc_info,
)

# 设置示例环境
setup_example_environment()

# 然后导入其他模块（此时 sys.path 已设置好）
from browser_use import Agent, BrowserSession, ChatOpenAI
from browser_use.browser import BrowserProfile
from config import get_settings
from runner import create_or_get_sandbox, set_sandbox_urls, get_vnc_viewer_url, destroy_sandbox


async def run_single_task(browser_session, llm, logger, task_description, task):
    """执行单个任务"""
    print_section(f"📝 任务: {task_description}")
    
    logger.info(f"📝 执行任务: {task_description}")
    
    agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser_session,
        use_vision=True,
        extend_system_message='过程使用中文，将结果详细输出'
    )
    
    result = await agent.run()
    final_result = result.final_result()
    
    print(f"\n✅ 结果：")
    print_result(final_result)
    
    logger.info(f"✅ {task_description} 完成")
    
    return {
        "task": task_description,
        "result": final_result,
        "steps": len(result.model_thoughts())
    }


async def example_single_task():
    """示例 1: 执行单个任务"""
    settings = get_settings()
    
    print_section("📝 示例 1: 执行单个任务")
    
    # 创建 Sandbox
    sandbox = create_or_get_sandbox(
        user_id="advanced_user",
        session_id="advanced_session",
        thread_id="task1"
    )
    
    logger = create_logger(session_id=sandbox['sandbox_id'])
    
    # 设置 CDP URL 和 VNC URL 到 VNC Server
    if sandbox.get('cdp_url') or sandbox.get('vnc_url'):
        set_sandbox_urls(
            sandbox_id=sandbox['sandbox_id'],
            cdp_url=sandbox.get('cdp_url'),
            vnc_url=sandbox.get('vnc_url')
        )
        
        if sandbox.get('vnc_url'):
            viewer_url = get_vnc_viewer_url(sandbox['sandbox_id'])
            print_vnc_info(viewer_url)
    
    try:
        # 创建 Browser Session
        browser_session = BrowserSession(
            cdp_url=sandbox['cdp_url'],
            browser_profile=BrowserProfile(
                headless=settings.browser_headless,
                timeout=settings.browser_timeout,
                keep_alive=True,
            )
        )
        
        llm = ChatOpenAI(
            model=settings.qwen_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        
        task = """
访问 https://www.aliyun.com/product/list 页面，完成以下任务：
1. 找到"计算"分类
2. 列出该分类下的前 3 个产品名称
3. 简要说明这些产品的主要用途

请用简洁的格式输出结果。
"""
        
        result = await run_single_task(
            browser_session, llm, logger,
            "阿里云产品信息提取", task
        )
        
        print(f"\n📊 任务统计：")
        print_info("执行步骤", result['steps'])
        
        # 清理
        await browser_session.stop()
        
        return result
        
    finally:
        destroy_sandbox(sandbox['sandbox_id'])


async def example_multiple_tasks():
    """示例 2: 顺序执行多个任务（复用 Sandbox）"""
    settings = get_settings()
    
    print_section("📝 示例 2: 顺序执行多个任务")
    
    # 创建 Sandbox（同一个 session，复用）
    sandbox = create_or_get_sandbox(
        user_id="advanced_user",
        session_id="advanced_session",  # 相同的 session
        thread_id="multitask"
    )
    
    logger = create_logger(session_id=sandbox['sandbox_id'])
    
    # 设置 CDP URL 和 VNC URL 到 VNC Server
    if sandbox.get('cdp_url') or sandbox.get('vnc_url'):
        set_sandbox_urls(
            sandbox_id=sandbox['sandbox_id'],
            cdp_url=sandbox.get('cdp_url'),
            vnc_url=sandbox.get('vnc_url')
        )
        
        if sandbox.get('vnc_url'):
            viewer_url = get_vnc_viewer_url(sandbox['sandbox_id'])
            print_vnc_info(viewer_url)
    
    # 定义多个任务
    tasks = [
        ("任务 1: 访问首页", "访问 https://www.aliyun.com 并提取首页的主标题"),
        ("任务 2: 产品菜单", "点击'产品'菜单，列出前 3 个产品分类名称"),
        ("任务 3: 解决方案", "找到'解决方案'相关的链接并说明")
    ]
    
    results = []
    
    try:
        # 创建 Browser Session（复用）
        browser_session = BrowserSession(
            dom_highlight_elements=True,
            cdp_url=sandbox['cdp_url'],
            browser_profile=BrowserProfile(
                headless=settings.browser_headless,
                timeout=settings.browser_timeout,
                keep_alive=True,
            )
        )
        
        llm = ChatOpenAI(
            model=settings.qwen_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        
        # 执行所有任务
        for task_desc, task_content in tasks:
            try:
                result = await run_single_task(
                    browser_session, llm, logger,
                    task_desc, task_content
                )
                results.append(result)
            except Exception as e:
                print(f"\n❌ {task_desc} 失败：{e}")
                logger.error(f"❌ {task_desc} 失败: {str(e)}")
                results.append({
                    "task": task_desc,
                    "error": str(e)
                })
        
        # 输出汇总
        print_section("📊 多任务执行汇总")
        
        success_count = sum(1 for r in results if 'result' in r)
        total_steps = sum(r.get('steps', 0) for r in results if 'result' in r)
        
        print(f"\n✅ 成功：{success_count}/{len(tasks)} 个任务")
        print_info("总步骤数", total_steps)
        
        # 清理
        await browser_session.stop()
        
        return results
        
    finally:
        destroy_sandbox(sandbox['sandbox_id'])


async def main():
    """主函数 - 运行所有示例"""
    
    # 验证配置
    settings = get_settings()
    
    if not validate_settings(settings):
        return
    
    print_section("🚀 AgentRun Browser Sandbox - BrowserUse 高级示例")
    print(f"\n📋 配置：")
    print_info("模型", settings.qwen_model)
    
    print("\n📚 本示例包含 2 个演示：")
    print("   1️⃣  执行单个任务")
    print("   2️⃣  顺序执行多个任务")
    
    # 让用户选择要运行的示例
    print("\n" + "="*60)
    choice = input("请选择要运行的示例（1-2，或按 Enter 运行全部）：").strip()
    
    try:
        if choice == "1":
            await example_single_task()
        elif choice == "2":
            await example_multiple_tasks()
        else:
            # 运行全部示例
            print("\n🔄 运行全部示例...\n")
            await example_single_task()
            await example_multiple_tasks()
        
        print_section("✨ 所有示例执行完成！")
        
    except Exception as e:
        print(f"\n❌ 执行出错：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n💡 提示：程序会在退出时自动清理 Sandbox 资源")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        # 注意: runner.py 中的 atexit 和 signal handler 会自动清理 sandbox
    except Exception as e:
        print(f"\n\n❌ 执行出错：{e}")
        import traceback
        traceback.print_exc()
        # 注意: runner.py 中的 atexit 会自动清理 sandbox
