# prime-agent-stripe-mcp

**Official [Stripe](https://stripe.com) MCP integration for Prime Agent.**

[![CI](https://github.com/gbrlpzz/prime-agent-stripe-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/gbrlpzz/prime-agent-stripe-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

Prime Agent connects to Stripe's official remote MCP server at
`https://mcp.stripe.com`. The agent can then inspect and manage Stripe
resources through the same API surface as other MCP clients.

> [!NOTE]
> Stripe's MCP server is in public preview. It exposes both read and write
> tools. Keep the connection in test mode while developing.

```
┌─────────────────────────────────┐                      ┌─────────────────────────────────┐
│ │ from stripe import         │  │                      │ │ mcp.stripe.com              │ │
│ │   stripe                   │  │                      │ │ API · billing · reporting   │ │
│ │ await stripe.list_tools()  │──┼   OAuth 2.1 + PKCE   │ │ products · customers        │ │
│ │ await stripe.call_tool(    │  │                      │ │ subscriptions · events      │ │
│ auth.json: mcp:stripe           │                      │ │ documentation search        │ │
└─────────────────────────────────┘                      └─────────────────────────────────┘
```

## Why this integration

- **Stripe-hosted server** — no self-hosted proxy and no Stripe API key in
  this repository.
- **Prime Agent-native** — the module extends `McpIntegration` and exposes
  the live tool inventory from the Python kernel.
- **OAuth 2.1 with PKCE** — the browser approval is stored only in Prime
  Agent's private `auth.json` under `mcp:stripe`.
- **Test-mode friendly** — authorize the Liminal Stripe account and use only
  test-mode resources during development.

## Install

Requires [Prime Agent](https://github.com/gbrlpzz/prime-agent-setup) with its
Python kernel and Python 3.10 or newer.

1. Clone the repository and link the skill into place:

   ```bash
   git clone https://github.com/gbrlpzz/prime-agent-stripe-mcp.git ~/prime-agent-stripe-mcp
   rm -rf ~/.agents/skills/stripe
   ln -s ~/prime-agent-stripe-mcp ~/.agents/skills/stripe
   ```

2. Install the editable package into Prime Agent's kernel environment:

   ```bash
   uv pip install --python ~/.prime/agent/kernel-venv/bin/python -e ~/prime-agent-stripe-mcp
   ```

3. Add the remote server to Prime Agent's MCP settings once:

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

4. Reload Prime Agent and authorize the Stripe account:

   ```text
   /reload
   /mcp login stripe
   ```

Approve the **Liminal Stripe account**, not a personal or production account
that should stay outside this development workflow. Prime Agent stores the
credential as `mcp:stripe`. It is never written to this repository.

## Usage

```python
from stripe import stripe, auth_status

print(auth_status())               # credential state, no token values
tools = await stripe.list_tools()  # live Stripe MCP inventory
# Inspect the live schema before calling a read or write tool.
result = await stripe.call_tool("<live-tool-name>", {"<live-argument>": "..."})
```

`auth_status()` returns a small dict without secrets:

```python
{"enabled": True, "expires_fresh": True, "type": "oauth"}
```

Tool names and parameters belong to Stripe and may change during the public
preview. Call `list_tools()` first, or use the methods bound automatically
from the live inventory.

The server includes tools for Stripe API discovery, API reads and writes,
account information, billing resources, documentation, and reporting. Write
operations change Stripe data. Ask for human confirmation before creating,
updating, cancelling, refunding, or deleting anything.

### Token refresh fallback

Prime Agent refreshes the stored token automatically. On hosts where that is
unavailable, call the module-level fallback:

```python
from stripe import refresh

refresh()  # exchanges the stored refresh token; rewrites auth.json with mode 600
```

## Liminal development workflow

1. Add your personal user as a team member of the Liminal Stripe account.
2. Authorize this integration as that user.
3. Confirm the Stripe dashboard is in **test mode**.
4. Create test products, prices, customers, and subscriptions only.
5. Configure the Supabase `stripe-webhook` function with the resulting test
   webhook signing secret separately. The MCP credential does not replace the
   server-side `STRIPE_SECRET_KEY` or `STRIPE_WEBHOOK_SECRET`.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `auth_status()` reports no credentials | Run `/mcp login stripe` again. |
| Calls fail after a long pause | Run `refresh()`; log in again if it returns `False`. |
| A tool name is unknown | Re-run `await stripe.list_tools()`; the inventory can change during preview. |

## Development

```bash
python3 tests/test_skill.py                             # standalone suite, no Prime Agent needed
~/.prime/agent/kernel-venv/bin/python -m pytest tests/  # inside Prime Agent's kernel
```

CI runs the standalone suite on every push to `main`.

## Security

- No credentials live in this repository or its Git history.
- OAuth tokens live only in Prime Agent's private `auth.json`.
- The module talks only to `https://mcp.stripe.com` and Stripe's OAuth
  authorization server.
- Keep all development mutations in Stripe test mode.
- Never put Stripe secret values or private-key material in source, tests,
  documentation, or Git history.

## License

MIT — see [LICENSE](LICENSE). Stripe is a trademark of Stripe, Inc.; this is
an independent client integration for Stripe's official MCP server (see
[NOTICE](NOTICE)).
