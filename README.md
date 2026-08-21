# stripe-mcp

**Official [Stripe](https://stripe.com) MCP integration for Prime Agent.** The
agent connects to Stripe's own remote MCP server, so it can inspect and manage
Stripe resources through the same API surface as other supported MCP clients.

> Stripe's MCP server is currently in public preview. It exposes both read and
> write API tools. Keep the connection in test mode while developing.

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  Prime Agent kernel          │        │  Stripe (official, remote)   │
│  ┌────────────────────────┐  │  OAuth │  ┌──────────────────────────┐ │
│  │ from stripe import     │  │ 2.1    │  │ mcp.stripe.com           │ │
│  │   stripe               │──┼───────▶│  │ API · billing · docs      │ │
│  │ await stripe.list_…() │  │ PKCE   │  │ products · customers      │ │
│  └────────────────────────┘  │        │  │ subscriptions · events   │ │
│  auth.json: mcp:stripe       │        │  └──────────────────────────┘ │
└──────────────────────────────┘        └──────────────────────────────┘
```

## Why this integration

- **Stripe-hosted MCP server** — no self-hosted proxy and no Stripe API key in
  this repository.
- **Prime Agent-native** — auto-discovers the live tool inventory through
  `McpIntegration` and exposes it from the Python kernel.
- **OAuth** — the browser approval is stored only in Prime Agent's private
  `auth.json` under `mcp:stripe`.
- **Test-mode friendly** — authorize the Liminal Stripe account and use only
  test-mode resources during development.

## Install

Requires [Prime Agent](https://github.com/gbrlpzz/prime-agent-setup) with its
Python kernel (`rlm`).

```bash
# 1. clone and link the skill into place
git clone https://github.com/gbrlpzz/prime-agent-stripe-mcp.git ~/prime-agent-stripe-mcp
rm -rf ~/.agents/skills/stripe
ln -s ~/prime-agent-stripe-mcp ~/.agents/skills/stripe

# 2. install the editable package into Prime Agent's kernel
uv pip install --python ~/.prime/agent/kernel-venv/bin/python -e ~/prime-agent-stripe-mcp
```

Add the remote server to Prime Agent's MCP settings once:

```json
{
  "mcpServers": {
    "stripe": {
      "type": "http",
      "url": "https://mcp.stripe.com",
      "oauth": true
    }
  }
}
```

Then reload Prime Agent and authorize the Stripe account:

```text
/reload
/mcp login stripe
```

Approve the **Liminal Stripe account**, not a personal or production account
that should remain outside this development workflow.

The credential is stored by Prime Agent as `mcp:stripe`. It is never written to
this repository.

## Usage

```python
from stripe import stripe, auth_status

print(auth_status())              # no credentials are printed
tools = await stripe.list_tools() # live Stripe MCP inventory
# Inspect the live schema before calling a read or write tool.
result = await stripe.call_tool("<live-tool-name>", {"<live-argument>": "..."})
```

Tool names and parameters are owned by Stripe and may change during public
preview. Call `list_tools()` first or use the auto-bound methods exposed by the
live inventory.

The server includes tools for Stripe API discovery, API reads and writes,
account information, billing resources, documentation, and reporting. Write
operations can change Stripe data. Require human confirmation before creating,
updating, cancelling, refunding, or deleting anything.

## Liminal development workflow

1. Add your personal user as a team member of the Liminal Stripe account.
2. Authorize this integration as that user.
3. Confirm the Stripe dashboard is in **test mode**.
4. Create test products, prices, customers, and subscriptions only.
5. Configure the Supabase `stripe-webhook` function with the resulting test
   webhook signing secret separately. The MCP credential does not replace the
   server-side `STRIPE_SECRET_KEY` or `STRIPE_WEBHOOK_SECRET`.

## Authentication and refresh

The official server publishes standard OAuth metadata at Stripe's access
server. Prime Agent's generic OAuth client handles PKCE, dynamic registration,
token storage, and automatic refresh. The module also exposes `refresh()` as a
small fallback for hosts where automatic refresh is unavailable.

## Development

```bash
python3 tests/test_skill.py
~/.prime/agent/kernel-venv/bin/python -m pytest tests/
```

CI runs the standalone test suite on every push.

## Security

- No credentials are stored in this repository or committed to git.
- OAuth tokens live only in Prime Agent's private `auth.json`.
- The integration connects only to `https://mcp.stripe.com` and Stripe's OAuth
  authorization server.
- Keep all development mutations in Stripe test mode.
- Never put Stripe secret values or private-key material in source, tests,
  documentation, or Git history.

## License

MIT — see [LICENSE](LICENSE). Stripe is a trademark of Stripe, Inc.; this is an
independent client integration for Stripe's official MCP server (see
[NOTICE](NOTICE)).
