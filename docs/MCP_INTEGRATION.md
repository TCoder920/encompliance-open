# MCP Integration Guide

This document explains how to expose the EnCompliance platform to external AI tooling
such as ChatGPT via the Model Context Protocol (MCP).

## 1. Provision an API Key

1. Log in as a facility administrator with an active Pro/Enterprise subscription.
2. Navigate to **Settings → API Keys** (UI coming soon) or call `POST /api/v1/api-keys`.
3. Provide:
   - `label`: Human-readable name (e.g., `ChatGPT-Audit`).
   - `scopes`: Capabilities the key should have (`tasks:read`, `ai:forms`, etc.).
   - `expires_in_days`: Optional rotation window (1–365 days, default 90).
   - `ip_allowlist`: Optional list of static IPs permitted to use the key.
4. Store the returned `secret` securely—this is the only time it will be shown.

## 2. Available MCP Tools

| Tool Name             | Scope       | Description |
|----------------------|-------------|-------------|
| `listOperationalTasks` | `tasks:read` | Returns outstanding operational tasks for the mapped facility (limit 50). |
| `generateFormBlueprint` | `ai:forms` | Delegates to the AI form assistant to produce a compliance form template. |

More tools can be added by registering handlers in `app/mcp/server.py`.

## 3. MCP Endpoints

All MCP routes live under `/api/v1/mcp` (or `/api/mcp` for legacy clients) and require
the `X-API-Key` header.

### List Tools

```
POST /api/v1/mcp/tools/list
Headers: X-API-Key: <your secret>
```

### Execute a Tool

```
POST /api/v1/mcp/tools/execute
Headers: X-API-Key: <your secret>
Body:
{
  "tool_name": "listOperationalTasks",
  "arguments": { "limit": 5 }
}
```

## 4. Connecting from ChatGPT

1. Open [chat.openai.com](https://chat.openai.com) → **Explore GPTs** → *Create*.
2. In the **Actions** tab choose *Model Context Protocol* → *Add new tool*.
3. Supply:
   - **URL**: `https://<your-domain>/api/v1/mcp`
   - **API Key**: Value provisioned in step 1.
4. Test by invoking `listOperationalTasks`. ChatGPT should return structured data.

## 5. Security Practices

- Rotate API keys at least every 90 days.
- Restrict keys to the minimum scopes required for a GPT workflow.
- Enable IP allowlists for static endpoints such as ChatGPT Actions proxies.
- Monitor `client_logs.log` and the MCP audit table (future work) for unusual usage.

Refer to `docs/SECURITY.md` for operational procedures and alerting guidance.

