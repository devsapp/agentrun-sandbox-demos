#!/usr/bin/env python3
"""
调试脚本：创建 Sandbox -> 执行 Python 验证 -> 用 execute_shell_command 在 8005 端口启动 HTML 服务 -> 输出泛域名 -> 删除 Sandbox。
运行前请确保 assets/.env 已配置。从本目录运行：python test_run.py
"""
import os
import sys
import time

# 从本目录加载 assets/.env
_skill_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _skill_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(_skill_dir, "assets", ".env"))

# SDK 使用 AGENTRUN_*，.env 常用 ALIBABA_CLOUD_*，在此统一同步
if not os.getenv("AGENTRUN_REGION") and os.getenv("ALIBABA_CLOUD_REGION"):
    os.environ["AGENTRUN_REGION"] = os.environ["ALIBABA_CLOUD_REGION"]
# 确保 SDK 能读到账号 ID（AGENTRUN_ACCOUNT_ID 或 ALIBABA_CLOUD_ACCOUNT_ID）
if os.getenv("AGENTRUN_ACCOUNT_ID"):
    pass
elif os.getenv("ALIBABA_CLOUD_ACCOUNT_ID"):
    os.environ["AGENTRUN_ACCOUNT_ID"] = os.environ["ALIBABA_CLOUD_ACCOUNT_ID"]
else:
    # 尝试通过 STS GetCallerIdentity 从 AK/SK 获取 AccountId
    try:
        from alibabacloud_sts20150401.client import Client as StsClient
        from alibabacloud_credentials.client import Client as CredClient
        from alibabacloud_tea_openapi import models as open_api_models

        cred = CredClient()
        config = open_api_models.Config(
            access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
            region_id=os.getenv("ALIBABA_CLOUD_REGION", "cn-hangzhou"),
            endpoint="sts.aliyuncs.com",
        )
        sts = StsClient(config)
        r = sts.get_caller_identity()
        if r.body and getattr(r.body, "account_id", None):
            os.environ["AGENTRUN_ACCOUNT_ID"] = r.body.account_id
            print(f"[自动] 从 STS 获取 AccountId: {r.body.account_id}")
    except Exception as e:
        print("请在 assets/.env 中设置 ALIBABA_CLOUD_ACCOUNT_ID 或 AGENTRUN_ACCOUNT_ID（阿里云主账号 ID）")
        print(f"  或确保已安装: pip install alibabacloud_sts20150401 alibabacloud_credentials（自动获取失败: {e}）")
        sys.exit(1)
if not os.getenv("AGENTRUN_ACCOUNT_ID"):
    print("请在 assets/.env 中设置 ALIBABA_CLOUD_ACCOUNT_ID 或 AGENTRUN_ACCOUNT_ID")
    sys.exit(1)

from src.sandbox_lifecycle import create_sandbox, destroy_sandbox
from src.executor import execute_python_code, execute_shell_command
from src.domain import sandbox_port_domain


def main():
    sandbox = None
    sandbox_id = None
    base_url = None

    print("=== 1. 创建 Sandbox ===")
    try:
        sandbox, sandbox_id, base_url = create_sandbox(idle_timeout_seconds=600)
        print(f"  sandbox_id: {sandbox_id}")
        print(f"  base_url:  {base_url}")
    except Exception as e:
        print(f"  创建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    if not base_url:
        print("  [WARN] base_url 为空，execute 可能失败；尝试从 CDP URL 解析")
        if hasattr(sandbox, "get_cdp_url"):
            try:
                cdp = sandbox.get_cdp_url()
                print(f"  cdp_url: {cdp}")
            except Exception as e2:
                print(f"  get_cdp_url 失败: {e2}")

    # 等待 Sandbox 就绪后再调用 execute（避免 502）
    print("  等待 Sandbox 就绪（5s）...")
    time.sleep(5)

    _base = base_url
    if not _base and sandbox_id:
        acc = os.getenv("AGENTRUN_ACCOUNT_ID") or os.getenv("ALIBABA_CLOUD_ACCOUNT_ID")
        reg = os.getenv("ALIBABA_CLOUD_REGION", "cn-hangzhou")
        if acc:
            _base = f"https://{acc}.agentrun-data.{reg}.aliyuncs.com/sandboxes/{sandbox_id}"
    print("\n=== 2. 执行简单 Python 代码（验证 execute）===")
    _url = _base or f"https://agentrun-data.cn-hangzhou.aliyuncs.com/sandboxes/{sandbox_id}"
    r = None
    for attempt in range(1, 4):
        try:
            r = execute_python_code(_url, code="print(1+1)")
            print(f"  status: {r.get('status')}")
            print(f"  stdout: {r.get('result', {}).get('stdout', '').strip() or '(空)'}")
            if r.get("status") != "completed":
                print(f"  stderr: {r.get('result', {}).get('stderr', '')}")
            break
        except Exception as e:
            err_str = str(e)
            if "502" in err_str and attempt < 3:
                print(f"  第 {attempt} 次 502，{5 * attempt}s 后重试...")
                time.sleep(5 * attempt)
                continue
            print(f"  执行失败: {e}")
            import traceback
            traceback.print_exc()
            destroy_sandbox(sandbox)
            return 1
    if r is None:
        destroy_sandbox(sandbox)
        return 1

    print("\n=== 3. 用 execute_shell_command 在 8005 端口启动 HTML 服务 ===")
    base = _base
    server_ok = False
    # 在 /tmp/www8005 写入 index.html，再后台启动 python3 -m http.server 8005
    shell_cmd = (
        "mkdir -p /tmp/www8005 && "
        "echo '<!DOCTYPE html><html><head><meta charset=utf-8><title>Sandbox 8005</title></head>"
        "<body><h1>OK from sandbox port 8005</h1><p>execute_shell_command 验证</p></body></html>' > /tmp/www8005/index.html && "
        "nohup python3 -m http.server 8005 --bind 0.0.0.0 --directory /tmp/www8005 > /tmp/srv8005.log 2>&1 & "
        "sleep 1 && echo 'HTTP server started on 0.0.0.0:8005'"
    )
    for attempt in range(1, 4):
        try:
            r2 = execute_shell_command(base, command=shell_cmd, timeout=20.0)
            server_ok = r2.get("status") == "completed"
            print(f"  status: {r2.get('status')}, stdout: {r2.get('result', {}).get('stdout', '').strip() or '(空)'}")
            if r2.get("result", {}).get("stderr"):
                print(f"  stderr: {r2.get('result', {}).get('stderr')}")
            break
        except Exception as e:
            if "502" in str(e) and attempt < 3:
                print(f"  第 {attempt} 次 502，{3 * attempt}s 后重试...")
                time.sleep(3 * attempt)
                continue
            print(f"  启动失败: {e}")
            break

    if not server_ok:
        print("  [WARN] HTTP 服务启动可能未成功，仍将输出泛域名供你测试。")

    wildcard = os.getenv("SANDBOX_WILDCARD_DOMAIN", "test.functioncompute.com")
    domain = sandbox_port_domain(wildcard, 8005, sandbox_id)
    print("\n=== 4. 多端口泛域名（用于访问 8005 HTML 服务）===")
    print(f"  {domain}")
    print("  在浏览器打开 https://" + domain + " 可验证 HTML 页面。")
    print("  若看到「Welcome to OpenResty」：请求未进入 Sandbox，被网关默认页拦截。")
    print("  需在 AgentRun/FC 控制台确认：泛域名 8005-{sandbox_id} 是否已配置为转发到该 Sandbox 的 8005 端口。")
    if sys.stdin.isatty():
        try:
            input("\n按 Enter 将删除 Sandbox 并退出（或 Ctrl+C 保留 Sandbox）...")
        except KeyboardInterrupt:
            print("\n已跳过删除，Sandbox 仍运行，可继续用上述域名测试。")
            return 0

    print("\n=== 5. 删除 Sandbox ===")
    try:
        destroy_sandbox(sandbox)
        print("  删除成功")
    except Exception as e:
        print(f"  删除失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n全部步骤完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
