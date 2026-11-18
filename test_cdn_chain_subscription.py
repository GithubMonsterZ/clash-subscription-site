"""Check optional CDN-chain isolation and credential-safe export boundaries."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class CdnChainExport(unittest.TestCase):
    def setUp(self):
        self.node = {"type": "vless", "server": "example.com", "port": 2087,
                     "uuid": "6f8bcb7c-47fb-47cb-bdda-fb5ba0a03de1", "network": "ws",
                     "tls": True, "skip-cert-verify": False, "servername": "example.com",
                     "alpn": ["http/1.1"],
                     "ws-opts": {"path": "/test/chain", "headers": {"Host": "example.com"}}}
        self.base = {"SUBSCRIPTION_TOKEN": "A" * 43,
                     "DMIT_NODE_JSON": json.dumps(self.node)}
        self.added = {"VPS38_CDN_CHAIN_NODE_JSON": json.dumps(self.node),
                      "VPS38_CDN_CHAIN_SUBSCRIPTION_TOKEN": "B" * 43}

    def build(self, extra):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            shutil.copy2(Path(__file__).with_name("build.py"), path / "build.py")
            clean = {k: v for k, v in os.environ.items()
                     if not k.endswith(("_NODE_JSON", "_SUBSCRIPTION_TOKEN"))
                     and k not in ("FULL_CONFIG_JSON", "SUBSCRIPTION_TOKEN")}
            run = subprocess.run(["python3", str(path / "build.py")],
                                 env={**clean, **self.base, **extra}, capture_output=True)
            files = {str(p.relative_to(path / "public")): p.read_bytes()
                     for p in (path / "public").rglob("*") if p.is_file()}
            return run.returncode, files

    def test_addition_preserves_existing_export(self):
        old_status, old = self.build({})
        status, new = self.build(self.added)
        self.assertEqual((old_status, status), (0, 0))
        self.assertTrue(all(new[key] == value for key, value in old.items()))
        added = set(new) - set(old)
        self.assertEqual(added, {"s/" + "B" * 43 + "/clash.yaml"})
        node = json.loads(new[added.pop()])["proxies"][0]
        self.assertEqual(node, dict(self.node, name="vps38-vps67"))

    def test_reject_incomplete_duplicate_or_insecure_configuration(self):
        bad = [dict(self.added, VPS38_CDN_CHAIN_SUBSCRIPTION_TOKEN="A" * 43),
               {"VPS38_CDN_CHAIN_NODE_JSON": json.dumps(self.node)},
               {"VPS38_CDN_CHAIN_SUBSCRIPTION_TOKEN": "B" * 43},
               dict(self.added, VPS38_CDN_CHAIN_NODE_JSON=json.dumps(
                   dict(self.node, **{"skip-cert-verify": True}))),
               dict(self.added, VPS38_CHAIN_NODE_JSON=json.dumps(self.node),
                    VPS38_CHAIN_SUBSCRIPTION_TOKEN="B" * 43)]
        for extra in bad:
            with self.subTest(keys=sorted(extra)):
                self.assertNotEqual(self.build(extra)[0], 0)


if __name__ == "__main__":
    unittest.main()
