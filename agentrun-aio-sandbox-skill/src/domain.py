"""
多端口 Sandbox 域名生成

规则：{端口}-{sandboxID}.{泛域名}
"""


def sandbox_port_domain(
    wildcard_domain: str,
    port: int | str,
    sandbox_id: str,
) -> str:
    """
    按规则生成多端口访问域名。

    Args:
        wildcard_domain: 泛域名，如 sandbox.example.com（可含协议，会被去掉）
        port: 端口号
        sandbox_id: Sandbox ID

    Returns:
        {port}-{sandbox_id}.{wildcard_domain}
    """
    domain = wildcard_domain.strip().lower()
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix) :]
            break
    domain = domain.split("/")[0]
    return f"{port}-{sandbox_id}.{domain}"
