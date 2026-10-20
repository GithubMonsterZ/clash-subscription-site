"""Build a Clash/Mihomo subscription from Render environment secrets."""
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import uuid


def full_subscription(single_token):
    """Accept a separately authorized full-chain export, never publish it at root."""
    raw = os.environ.get("FULL_CONFIG_JSON")
    token = os.environ.get("FULL_SUBSCRIPTION_TOKEN")
    if raw is None and token is None:
        return None
    if raw is None or token is None:
        raise ValueError("Both full subscription environment variables are required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token) or token == single_token:
        raise ValueError("Invalid or duplicate full subscription token")
    config = json.loads(raw)
    fields = {"mode", "log-level", "ipv6", "unified-delay", "dns", "rules",
              "mixed-port", "allow-lan", "bind-address", "find-process-mode",
              "profile", "proxies", "proxy-groups"}
    if set(config) - fields:
        raise ValueError("Unexpected full configuration settings")
    if config.get("allow-lan") is not False or config.get("bind-address") != "127.0.0.1":
        raise ValueError("Full configuration must bind loopback only")
    if config.get("mode") != "rule" or len(config.get("proxies", [])) != 2:
        raise ValueError("Expected a two-node rule configuration")
    nodes = config["proxies"]
    node_fields = {"name", "type", "server", "port", "uuid", "network", "tls",
                   "udp", "flow", "servername", "client-fingerprint", "reality-opts", "dialer-proxy"}
    for node in nodes:
        if set(node) - node_fields or node.get("type") != "vless" or node.get("tls") is not True:
            raise ValueError("Invalid full-chain node")
        uuid.UUID(node["uuid"])
    by_name = {node["name"]: node for node in nodes}
    front, exit_name = "DMIT美国优化10/16", "DMIT → v128直出"
    if set(by_name) != {front, exit_name} or "dialer-proxy" in by_name[front]:
        raise ValueError("Unexpected chain structure")
    if by_name[exit_name].get("dialer-proxy") != front:
        raise ValueError("Missing DMIT front proxy")
    if config.get("proxy-groups") != [{"name": "Proxy", "type": "select", "proxies": [exit_name]}]:
        raise ValueError("Full subscription must select the chained exit")
    if not isinstance(config.get("rules"), list) or config["rules"][-1:] != ["MATCH,Proxy"]:
        raise ValueError("Missing full routing rules")
    return token, config


def single_config(source, name):
    fields = {"name", "type", "server", "port", "uuid", "network", "tls",
              "udp", "flow", "servername", "client-fingerprint", "reality-opts"}
    node = {k: v for k, v in source.items() if k in fields}
    if node["type"] != "vless" or node["tls"] is not True:
        raise ValueError("Expected VLESS with TLS")
    uuid.UUID(node["uuid"])
    if not isinstance(node["port"], int) or not 1 <= node["port"] <= 65535:
        raise ValueError("Invalid node port")
    node["name"] = name
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
    return config


def build():
    token = os.environ["SUBSCRIPTION_TOKEN"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise ValueError("Invalid subscription token")
    config = single_config(json.loads(os.environ["DMIT_NODE_JSON"]), "DMIT美国优化10/16")
    full = full_subscription(token)
    extra = None
    extra_raw = os.environ.get("VPS38_NODE_JSON")
    extra_token = os.environ.get("VPS38_SUBSCRIPTION_TOKEN")
    if extra_raw is not None or extra_token is not None:
        if extra_raw is None or extra_token is None:
            raise ValueError("Both VPS38 environment variables are required")
        used_tokens = {token}
        if full:
            used_tokens.add(full[0])
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}", extra_token) or extra_token in used_tokens:
            raise ValueError("Invalid or duplicate VPS38 subscription token")
        extra = single_config(json.loads(extra_raw), "vps38-direct")
        # Modern REALITY servers require this key share; retain it only for
        # this explicitly configured endpoint, leaving older exports unchanged.
        if json.loads(extra_raw).get("reality-opts", {}).get("support-x25519mlkem768") is True:
            extra["proxies"][0]["reality-opts"]["support-x25519mlkem768"] = True
    # JSON is valid YAML; no YAML library or other build dependencies needed.
    out = Path(__file__).resolve().parent / "public"
    if out.exists():
        shutil.rmtree(out)
    (out / "s" / token).mkdir(parents=True)
    (out / "s" / token / "clash.yaml").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if full:
        full_token, full_config = full
        (out / "s" / full_token).mkdir()
        (out / "s" / full_token / "clash.yaml").write_text(json.dumps(full_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if extra is not None:
        (out / "s" / extra_token).mkdir()
        (out / "s" / extra_token / "clash.yaml").write_text(json.dumps(extra, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "index.html").write_text('<!doctype html><meta name="robots" content="noindex,nofollow"><title>Subscription service</title><p>Use your subscription link in Clash Verge Rev.</p>\n', encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    print("Subscription built successfully.")


if __name__ == "__main__":
    build()
