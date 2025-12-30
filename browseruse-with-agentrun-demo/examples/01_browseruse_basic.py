"""
示例 1: BrowserUse 基础示例

这是最简单的 BrowserUse + Qwen 集成示例，展示如何：
1. 配置 Qwen 多模态模型
2. 创建浏览器会话
3. 执行简单的浏览器任务
4. 查看执行结果

运行方式：
    # 方式 1: 不使用 VNC Server（只需配置 .env）
    python examples/01_browseruse_basic.py
    
    # 方式 2: 使用 VNC Server 可视化（推荐）
    # 终端 1: python main.py
    # 终端 2: python examples/01_browseruse_basic.py

前提条件：
    1. 配置 .env 文件（参考 env.example）
    2. 获取 DashScope API Key
    3. 获取 Browser Sandbox CDP Endpoint
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
    print_sandbox_info,
    print_vnc_info,
    print_execution_stats,
    get_env_or_default
)

# 设置示例环境
setup_example_environment()

# 然后导入其他模块（此时 sys.path 已设置好）
from browser_use import Agent, BrowserSession, ChatOpenAI
from browser_use.browser import BrowserProfile
from config import get_settings
from runner import create_or_get_sandbox, set_sandbox_urls, get_vnc_viewer_url, destroy_sandbox


async def main():
    """主函数"""
    
    # 加载配置
    settings = get_settings()
    
    print_section("🚀 AgentRun Browser Sandbox - BrowserUse 基础示例")
    
    # 验证必要的配置
    if not validate_settings(settings):
        return
    
    # 创建 Sandbox
    sandbox = create_or_get_sandbox(
        user_id=get_env_or_default("USER_ID", "default_user"),
        session_id=get_env_or_default("SESSION_ID", "default_session"),
        thread_id=get_env_or_default("THREAD_ID", "default_thread"),
        template_name = get_env_or_default("TEMPLATE_NAME", "default_template")
    )
    
    # 创建 logger
    logger = create_logger(session_id=sandbox['sandbox_id'])
    
    # 设置 CDP URL 和 VNC URL 到 VNC Server（如果可用）
    viewer_url = None
    if sandbox.get('cdp_url') or sandbox.get('vnc_url'):
        set_sandbox_urls(
            sandbox_id=sandbox['sandbox_id'],
            cdp_url=sandbox.get('cdp_url'),
            vnc_url=sandbox.get('vnc_url')
        )
        
        if sandbox.get('vnc_url'):
            viewer_url = get_vnc_viewer_url(sandbox['sandbox_id'])
            logger.info(f"VNC Viewer: {viewer_url}")
            print_vnc_info(viewer_url)
    
    # 打印配置信息
    print(f"\n📋 配置信息：")
    print_info("模型", settings.qwen_model)
    print_info("CDP URL", sandbox['cdp_url'][:60] + "...")
    print_info("视觉能力", "✅ 已启用" if settings.browser_use_vision else "❌ 未启用")
    
    try:
        # 创建浏览器会话
        print(f"\n🌐 正在创建浏览器会话...")
        logger.info("📝 步骤 1: 创建浏览器会话")
        browser_session = BrowserSession(
            dom_highlight_elements=True,
            cdp_url=sandbox['cdp_url'],
            browser_profile=BrowserProfile(
                headless=settings.browser_headless,
                user_agent=settings.user_agent,
                timeout=settings.browser_timeout,
                keep_alive=True,
            )
        )
        
        # 配置大语言模型
        print(f"🤖 正在配置 {settings.qwen_model} 模型...")
        logger.info(f"📝 步骤 2: 配置 LLM - {settings.qwen_model}")
        llm = ChatOpenAI(
            model=settings.qwen_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        
        # 定义任务
        task = """
请访问 https://www.aliyun.com 网站，并完成以下任务：
1. 提取首页的主要产品分类
2. 找到"产品"或"解决方案"相关的导航菜单
3. 总结阿里云提供的主要服务类别

请用简洁的语言输出结果。
"""
        
        # 创建 Agent
        print(f"\n🎯 正在创建 Agent...")
        logger.info("📝 步骤 3: 创建 BrowserUse Agent")
        agent = Agent(
            task=task,
            llm=llm,
            browser_session=browser_session,

            use_vision=settings.browser_use_vision,
            extend_system_message='过程使用中文，将结果详细输出'
        )
        
        # 执行任务
        print(f"\n⏳ 开始执行任务...\n")
        print("💡 提示：您可以通过 VNC 实时查看浏览器操作")
        if sandbox.get('vnc_url'):
            print(f"   VNC Viewer: {viewer_url}")
        print()
        
        logger.info("📝 步骤 4: 开始执行浏览器任务")
        logger.info("🎯 任务: 访问阿里云官网并提取信息")
        result = await agent.run()
        
        # 输出结果
        print_section("📊 任务执行结果")
        
        final_result_text = result.final_result()
        print(f"\n✅ 最终结果：")
        print_result(final_result_text)
        
        # 记录结果到日志
        steps_count = len(result.model_thoughts())
        logger.info(f"✅ 任务执行完成 - 步骤数: {steps_count}, 结果长度: {len(final_result_text)}")
        
        # 输出统计信息
        print_execution_stats(result, show_tokens=True, show_thoughts=True, max_thoughts=3)
        
        # 输出执行的操作
        try:
            actions = result.model_actions_filtered()
            if actions:
                print(f"\n🔧 执行的操作：")
                print(f"   {actions}")
        except Exception:
            pass
        
        print("\n✨ 任务执行完成！")
        logger.info("✨ 示例执行完成")
        
    except Exception as e:
        print(f"\n❌ 任务执行失败：{e}")
        logger.error(f"❌ 任务执行失败: {str(e)}")
        raise
    
    finally:
        # 清理资源
        print("\n🧹 正在清理资源...")
        logger.info("🧹 清理浏览器会话")
        await browser_session.stop()
        
        # 销毁 Sandbox
        destroy_sandbox(sandbox['sandbox_id'])
        logger.info("✅ 资源清理完成")
        print("✅ 资源清理完成")


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" AgentRun Browser Sandbox - BrowserUse 基础示例")
    print("="*60)
    print("\n📚 本示例展示：")
    print("   1. 基础的 BrowserUse + Qwen 集成")
    print("   2. 简单的网页访问和信息提取")
    print("   3. 结果输出和统计信息展示")
    print("\n⏱️  预计耗时：1-3 分钟")
    print("\n💡 提示：程序会在退出时自动清理 Sandbox 资源")
    print()
    
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
