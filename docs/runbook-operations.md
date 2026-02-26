# Operations Runbook (M4)

## Purpose

Provide repeatable startup, validation, diagnostics, and rotation touchpoints for operating `mcp-auth-broker` in containerized environments.

## Startup

### Local runtime

```bash
python -m mcp_auth_broker.cli
python -m mcp_auth_broker.cli health
python -m mcp_auth_broker.cli ready
```

### Container runtime

```bash
docker build -t mcp-auth-broker:local .
docker run --rm mcp-auth-broker:local python -m mcp_auth_broker.cli health
```

## Required Configuration

- `MCP_AUTH_BROKER_ENV`
- `MCP_AUTH_BROKER_ALLOWED_SCOPES`
- `MCP_AUTH_BROKER_ALLOWED_GRAPH_RESOURCES`
- `MCP_AUTH_BROKER_GRAPH_CLIENT_ID`
- `MCP_AUTH_BROKER_GRAPH_SECRET_REF`
- `MCP_AUTH_BROKER_SECRET_PROVIDER` (`none|1password`)
- `OP_SERVICE_ACCOUNT_TOKEN` (when `1password` mode is enabled)

## Operational Diagnostics

- Health/readiness:
  - `python -m mcp_auth_broker.cli health`
  - `python -m mcp_auth_broker.cli ready`
- Tool discovery:
  - `python -m mcp_auth_broker.cli tools`
- End-to-end smoke path:
  - `python -m mcp_auth_broker.cli smoke-e2e`
  - `./scripts/container-smoke-e2e.sh`
  - Note: smoke-e2e uses deterministic in-process smoke providers and validates broker orchestration flow, not live 1Password/Graph integration.

## Hardening Verification Checklist

- Redaction verification tests pass (`tests/test_redaction.py`).
- Repository secret scanning passes (`gitleaks` in CI).
- Dependency vulnerability scan passes (`pip-audit --strict`).
- License policy scan passes (`python scripts/check_licenses.py`).
- Container smoke E2E passes in CI.

## Secret and Credential Rotation Touchpoints

- Rotate `OP_SERVICE_ACCOUNT_TOKEN` according to organizational policy.
- Rotate Graph app credentials referenced by `MCP_AUTH_BROKER_GRAPH_SECRET_REF`.
- Verify post-rotation startup and smoke-e2e checks.

## Failure Scenarios

- `secret.*` errors: validate service-account token and secret reference path.
- `provider.*` errors: validate Graph app credentials and network access to login endpoint.
- `policy.*` denials: verify allowed resources/scopes configuration.

## Recovery Pattern

1. Confirm env configuration and secret references.
2. Run `health`, `ready`, and `smoke-e2e` checks.
3. Review structured audit output for deterministic error code.
4. Re-run CI hardening checks locally if needed.
