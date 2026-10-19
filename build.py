"""Build a Clash/Mihomo subscription from Render environment secrets."""
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import uuid


def build():
    token = os.environ["SUBSCRIPTION_TOKEN"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise ValueError("Invalid subscription token")
    source = json.loads(os.environ["DMIT_NODE_JSON"])
    fields = {"name", "type", "server", "port", "uuid", "network", "tls",
              "udp", "flow", "servername", "client-fingerprint", "reality-opts"}
    node = {k: v for k, v in source.items() if k in fields}
    if node["type"] != "vless" or node["tls"] is not True:
        raise ValueError("Expected VLESS with TLS")
    uuid.UUID(node["uuid"])
    if not isinstance(node["port"], int) or not 1 <= node["port"] <= 65535:
        raise ValueError("Invalid node port")
    node["name"] = "DMIT美国优化10/16"
    node["reality-opts"] = {k: node["reality-opts"][k] for k in ("public-key", "short-id")}
    rules = ["IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
             "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
             "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
             "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
             "IP-CIDR,169.254.0.0/16,DIRECT,no-resolve"]
    try:
        addr = ipaddress.ip_address(node["server"])
        rules.append(f"IP-CIDR{'6' if addr.version == 6 else ''},{addr}/{addr.max_prefixlen},DIRECT,no-resolve")
    except ValueError:
        rules.append(f"DOMAIN,{node['server']},DIRECT")
    rules.extend(["DOMAIN-SUFFIX,cn,DIRECT", "GEOIP,CN,DIRECT", "MATCH,Proxy"])
    config = {
        "mixed-port": 7890, "allow-lan": False, "mode": "rule",
        "log-level": "info", "ipv6": False,
        "profile": {"store-selected": True},
        "dns": {"enable": True, "ipv6": False, "enhanced-mode": "fake-ip",
                "fake-ip-range": "198.18.0.1/16",
                "fake-ip-filter": ["*.lan", "*.local", "localhost", "*.msftconnecttest.com", "*.msftncsi.com"],
                "default-nameserver": ["https://223.5.5.5/dns-query", "https://1.12.12.12/dns-query"],
                "proxy-server-nameserver": ["https://223.5.5.5/dns-query", "https://1.12.12.12/dns-query"],
                "nameserver": ["https://223.5.5.5/dns-query", "https://1.12.12.12/dns-query"],
                "fallback": ["https://1.1.1.1/dns-query#Proxy"],
                "fallback-filter": {"geoip": True, "geoip-code": "CN", "ipcidr": ["240.0.0.0/4"]}},
        "proxies": [node],
        "proxy-groups": [{"name": "Proxy", "type": "select", "proxies": [node["name"], "DIRECT"]}],
        "rules": rules,
    }
    # JSON is valid YAML; no YAML library or other build dependencies needed.
    out = Path(__file__).resolve().parent / "public"
    if out.exists():
        shutil.rmtree(out)
    (out / "s" / token).mkdir(parents=True)
    (out / "s" / token / "clash.yaml").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "index.html").write_text('<!doctype html><meta name="robots" content="noindex,nofollow"><title>Subscription service</title><p>Use your subscription link in Clash Verge Rev.</p>\n', encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    print("Subscription built successfully.")


if __name__ == "__main__":
    build()
