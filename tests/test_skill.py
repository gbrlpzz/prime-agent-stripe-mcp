#!/usr/bin/env python3
"""Standalone tests for the Prime Agent Stripe MCP integration."""

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))

try:
    import stripe as stripe_mod
    from stripe import STRIPE_MCP_URL, StripeMcp, auth_status, stripe

    HAS_RUNTIME = True
except Exception as exc:  # pragma: no cover - depends on local runtime
    HAS_RUNTIME = False
    _import_error = exc


class RepoStructureTest(unittest.TestCase):
    def test_required_files_exist(self):
        for name in (
            "README.md",
            "SKILL.md",
            "LICENSE",
            "NOTICE",
            "package.json",
            "pyproject.toml",
            "index.py",
            "src/stripe/__init__.py",
            "tests/test_skill.py",
        ):
            self.assertTrue((REPO / name).exists(), f"missing {name}")

    def test_license_is_pure_mit(self):
        text = (REPO / "LICENSE").read_text()
        self.assertTrue(text.startswith("MIT License\n\nCopyright (c) 2026"))
        self.assertIn("Permission is hereby granted", text)
        self.assertLess(len(text.splitlines()), 25)

    def test_package_json_metadata(self):
        package = json.loads((REPO / "package.json").read_text())
        self.assertEqual(package["python_import"], "stripe")
        self.assertEqual(package["callable"], "StripeMcp")
        self.assertEqual(package["main"], "index.py")

    def test_endpoint_and_no_credentials(self):
        text = "\n".join(
            p.read_text(errors="ignore")
            for p in REPO.rglob("*")
            if p.is_file() and ".git" not in p.parts
        )
        self.assertEqual(STRIPE_MCP_URL, "https://mcp.stripe.com")
        def marker(*parts: str) -> str:
            return "".join(parts)

        for secret_marker in (
            marker("BEGIN ", "PRIVATE KEY"),
            marker("BEGIN RSA ", "PRIVATE KEY"),
            marker("wh", "sec_"),
            marker("rk_", "live_"),
            marker("sk_", "live_"),
            marker("sk_", "test_123"),
        ):
            self.assertNotIn(secret_marker, text)


@unittest.skipUnless(HAS_RUNTIME, "Prime Agent runtime is not available")
class RuntimeIntegrationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.agent_dir = Path(self._tmp.name)
        from unittest import mock

        self._patch = mock.patch.object(stripe_mod, "_agent_dir", return_value=self.agent_dir)
        self._patch.start()
        self.addCleanup(self._patch.stop)
        self.addCleanup(self._tmp.cleanup)

    def test_config(self):
        self.assertEqual(stripe.server, "stripe")
        self.assertEqual(stripe.url, STRIPE_MCP_URL)
        self.assertIsInstance(stripe, StripeMcp)

    def test_auth_status_without_credentials(self):
        self.assertFalse(auth_status()["enabled"])

    def test_auth_status_with_private_credential(self):
        credential = {
            "type": "oauth",
            "access": "token-placeholder",
            "refresh": "refresh-placeholder",
            "expires": int((time.time() + 3600) * 1000),
        }
        (self.agent_dir / "auth.json").write_text(json.dumps({"mcp:stripe": credential}))
        status = auth_status()
        self.assertTrue(status["enabled"])
        self.assertTrue(status["expires_fresh"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
