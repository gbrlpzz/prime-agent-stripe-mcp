---
name: stripe
description: Official Stripe MCP integration for Prime Agent. Connects to Stripe's remote MCP server at https://mcp.stripe.com with OAuth and exposes live Stripe API, billing, reporting, and documentation tools. Use for Stripe test-mode setup, products, prices, customers, subscriptions, billing portal configuration, webhook inspection, and Stripe documentation. Keep mutations in test mode and require confirmation for writes.
---

# Stripe (official MCP)

Connects to Stripe's official remote MCP server:

```text
https://mcp.stripe.com
```

The server is in public preview and uses standard OAuth 2.1 with PKCE and
streamable HTTP. It exposes a live tool inventory, including Stripe API reads
and writes, account information, billing resources, reports, and documentation.

## Authentication

Add this server entry to Prime Agent's MCP settings:

```json
"stripe": {
  "type": "http",
  "url": "https://mcp.stripe.com",
  "oauth": true
}
```

Then run:

```text
/mcp login stripe
```

The token is stored privately under `mcp:stripe` in Prime Agent's `auth.json`.
Invite the operating user to the Liminal Stripe team rather than sharing a
separate account password.

## Usage

```python
from stripe import stripe, auth_status

auth_status()
tools = await stripe.list_tools()
out = await stripe.call_tool("stripe_api_read", {...})
```

Tool names and schemas are discovered from Stripe at runtime. Always inspect
the live inventory before constructing a call.

## Safety

Stripe exposes write tools. Use Stripe test mode for development. Require
explicit confirmation before creating or changing products, prices, customers,
subscriptions, payment state, refunds, webhook endpoints, or account settings.
Never persist Stripe credentials in the repository or pass live secrets through
model context.
