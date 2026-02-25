# Runbook: 1Password Service Account Runtime Setup (M2)

## Purpose

Configure the broker to resolve secret references from 1Password using service-account mode selected in ADR-0001.

## Prerequisites

- 1Password service account token with least-privilege access to required vault items.
- `op` CLI installed in runtime environment and available on `PATH`.

## Required Environment Variables

- `MCP_AUTH_BROKER_SECRET_PROVIDER=1password`
- `MCP_AUTH_BROKER_GRAPH_SECRET_REF=op://<vault>/<item>/<field>`
- `OP_SERVICE_ACCOUNT_TOKEN=<token>`

Example:

```bash
export MCP_AUTH_BROKER_SECRET_PROVIDER=1password
export MCP_AUTH_BROKER_GRAPH_SECRET_REF=op://broker-secrets/graph-client/client-secret
export OP_SERVICE_ACCOUNT_TOKEN=***
```

## Validation

- Start broker: `python -m mcp_auth_broker.cli`
- Run request path that requires secret resolution.
- Expected behavior:
  - Success path continues to provider call.
  - Failures map to deterministic codes: `secret.not_found`, `secret.access_denied`, `secret.timeout`, `secret.unavailable`.

## Security Notes

- Never print or persist secret values.
- Broker error metadata includes only secret reference identifiers.
- Ensure token rotation policy is managed outside application code.
