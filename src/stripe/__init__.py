"""Official Stripe MCP integration for Prime Agent.

Connects to Stripe's official remote MCP server (https://mcp.stripe.com,
public preview) using OAuth 2.1 managed by the Prime Agent host.

Authentication (one-time): run ``/mcp login stripe`` and approve the Stripe
account. The token is stored in the host's private ``auth.json`` under
``mcp:stripe`` and refreshed automatically by the host.

Usage from the agent kernel::

    from stripe import stripe, auth_status

    auth_status()
    tools = await stripe.list_tools()
    out = await stripe.call_tool("stripe_api_read", {...})
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from rlm.mcp_base import McpIntegration
except ImportError:  # pragma: no cover - standalone CI without Prime Agent
    class McpIntegration:  # type: ignore[no-redef]
        pass

__all__ = ["StripeMcp", "stripe", "STRIPE_MCP_URL", "auth_status", "refresh"]

#: Official Stripe MCP endpoint (streamable HTTP + OAuth). Public preview.
STRIPE_MCP_URL = "https://mcp.stripe.com"
STRIPE_TOKEN_ENDPOINT = "https://access.stripe.com/mcp/oauth2/token"


class StripeMcp(McpIntegration):
    """Stripe's official MCP server: API, billing, reporting, and docs.

    ``server`` and ``url`` match Prime Agent's ``mcpServers`` entry so the
    host's credential store and refresh routing use ``mcp:stripe``.
    """

    server = "stripe"
    url = STRIPE_MCP_URL


#: Module-level singleton exposed to the Prime Agent kernel.
stripe = StripeMcp()


def _agent_dir() -> Path:
    """Resolve the Prime Agent config directory like the runtime does."""
    raw = (
        os.environ.get("PRIME_AGENT_CODING_AGENT_DIR")
        or os.environ.get("PI_CODING_AGENT_DIR")
        or str(Path.home() / ".prime" / "agent")
    )
    return Path(raw).expanduser().resolve()


def auth_status() -> dict:
    """Return stored credential status without exposing token values."""
    try:
        auth = json.loads((_agent_dir() / "auth.json").read_text())
        cred = auth.get("mcp:stripe")
    except (OSError, ValueError):
        return {"enabled": False, "reason": "auth.json unreadable"}
    if not isinstance(cred, dict) or not cred.get("access"):
        return {
            "enabled": False,
            "reason": "no mcp:stripe credentials - run /mcp login stripe",
        }
    expires = cred.get("expires")
    fresh = isinstance(expires, (int, float)) and time.time() * 1000 < expires
    return {"enabled": True, "expires_fresh": fresh, "type": cred.get("type", "oauth")}


def refresh() -> bool:
    """Manually refresh the stored OAuth token as a host fallback.

    Prime Agent normally performs this through ``mcp.refresh``. This fallback
    follows Stripe's standard OAuth token exchange and rewrites only the
    private auth store, never the repository.
    """
    try:
        auth_path = _agent_dir() / "auth.json"
        auth = json.loads(auth_path.read_text())
        cred = auth.get("mcp:stripe")
        if not isinstance(cred, dict) or not cred.get("refresh"):
            return False
        data = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "refresh_token": cred["refresh"],
                "client_id": cred.get("clientId", ""),
            }
        ).encode()
        req = urllib.request.Request(
            cred.get("tokenEndpoint", STRIPE_TOKEN_ENDPOINT),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            token = json.loads(resp.read().decode())
        cred["access"] = token.get("access_token", cred.get("access"))
        cred["refresh"] = token.get("refresh_token") or cred.get("refresh", "")
        cred["expires"] = (
            int(time.time() * 1000)
            + int(token.get("expires_in", 3600)) * 1000
            - 5 * 60 * 1000
        )
        auth["mcp:stripe"] = cred
        auth_path.write_text(json.dumps(auth, indent=2))
        os.chmod(auth_path, 0o600)
        return True
    except Exception:
        return False
