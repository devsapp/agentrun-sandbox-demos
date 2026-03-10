#!/usr/bin/env python3
"""
多端口 Sandbox 域名生成

规则：{端口}-{sandboxID}.{泛域名}
用法：可从环境变量读取泛域名，或直接传入参数。
"""

import os
import sys

# 支持从本目录或项目根运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain import sandbox_port_domain


def main():
    # 4 个参数：脚本名 + wildcard_domain + port + sandbox_id
    if len(sys.argv) >= 4:
        wildcard_domain, port, sandbox_id = sys.argv[1], sys.argv[2], sys.argv[3]
        result = sandbox_port_domain(wildcard_domain, port, sandbox_id)
    # 3 个参数：脚本名 + port + sandbox_id（泛域名从环境变量读取）
    elif len(sys.argv) == 3:
        wildcard = os.getenv("SANDBOX_WILDCARD_DOMAIN", "")
        if not wildcard:
            print("Usage: sandbox_port_domain.py <wildcard_domain> <port> <sandbox_id>", file=sys.stderr)
            print("   or set SANDBOX_WILDCARD_DOMAIN and: sandbox_port_domain.py <port> <sandbox_id>", file=sys.stderr)
            sys.exit(1)
        port, sandbox_id = sys.argv[1], sys.argv[2]
        result = sandbox_port_domain(wildcard, port, sandbox_id)
    else:
        print("Usage: sandbox_port_domain.py <wildcard_domain> <port> <sandbox_id>", file=sys.stderr)
        print("   or set SANDBOX_WILDCARD_DOMAIN and: sandbox_port_domain.py <port> <sandbox_id>", file=sys.stderr)
        sys.exit(1)
    print(result)


if __name__ == "__main__":
    main()
