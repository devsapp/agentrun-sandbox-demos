"""
VNC Manager Server 启动入口

运行方式：
    python main.py              # 使用默认端口 8080
    python main.py 9000         # 指定端口 9000
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vncviewer import start_server


def main():
    """主函数"""
    
    # 打印欢迎信息
    print("""
╔═══════════════════════════════════════════════════════╗
║             VNC Manager Server                         ║
║                                                       ║
║  统一的 Sandbox 管理和可视化服务器                     ║
╚═══════════════════════════════════════════════════════╝
    """)
    
    # 获取端口（从命令行参数或使用默认值）
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1024 or port > 65535:
                print(f"⚠️  警告：端口 {port} 超出有效范围 (1024-65535)，使用默认端口 8080")
                port = 8080
        except ValueError:
            print(f"⚠️  警告：无效的端口号 '{sys.argv[1]}'，使用默认端口 8080")
            port = 8080
    
    print(f"📝 启动配置：")
    print(f"   端口: {port}")
    print(f"   主机: 0.0.0.0 (允许外部访问)")
    print()
    
    # 启动服务器
    try:
        start_server(
            host="0.0.0.0",
            port=port
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  收到中断信号，正在关闭服务器...")
        print("👋 服务器已关闭")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

