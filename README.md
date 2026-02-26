# mcp-auth-broker

Bootstrap baseline for the MCP Auth Broker implementation track.

## Runtime and Tooling

- Language/runtime: Python 3.12
- Package manager: `pip`
- Source layout: `src/` + `tests/`
- Quality tools: `ruff`, `pytest`

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

# Start scaffold runtime
python -m mcp_auth_broker.cli

# Health/readiness/tool discovery
python -m mcp_auth_broker.cli health
python -m mcp_auth_broker.cli ready
python -m mcp_auth_broker.cli tools
```

## Local Validation Commands

```bash
ruff format --check .
ruff check .
pytest
python scripts/check_licenses.py
./scripts/container-smoke-e2e.sh
docker build -t mcp-auth-broker:local .
```

## Bootstrap Documentation

- Decisions: `docs/bootstrap/decisions.md`
- Dependency policy: `docs/bootstrap/dependency-policy.md`

## Scaffold Capabilities (M1)

- MCP tool scaffold for `auth.graph.operation.execute.v1`
- Runtime config loading and validation from environment variables
- Middleware lifecycle hooks for policy and audit events
- Deterministic baseline policy behavior:
	- Allow reason: `policy.rule.allow.graph.user.read`
	- Deny reason: `policy.rule.deny.scope.not_permitted`

## Secret Provider (M2)

- Secret provider abstraction with 1Password service-account adapter
- Configure via environment:
	- `MCP_AUTH_BROKER_SECRET_PROVIDER=1password`
	- `MCP_AUTH_BROKER_GRAPH_SECRET_REF=op://<vault>/<item>/<field>`
	- `OP_SERVICE_ACCOUNT_TOKEN=<token>`
- Deterministic secret error codes:
	- `secret.not_found`
	- `secret.access_denied`
	- `secret.timeout`
	- `secret.unavailable`
- Setup runbook: `docs/runbook-1password-service-account.md`

## Graph Token Provider + Cache (M3)

- OAuth2 client-credentials token provider for Microsoft Graph
- In-memory cache keyed by tenant/client/scopes with:
	- pre-expiry skew safety buffer
	- max effective TTL clamp
	- no expired-token return
- Deterministic allowlist and provider error behavior:
	- provider allowlist deny: `policy.denied`
	- scope allowlist deny: `policy.invalid_scope`
	- token provider failures: `provider.auth_failed|provider.timeout|provider.unavailable|provider.bad_response`
- Token material is never returned in response payloads; only token metadata is emitted.

## M4 Hardening and Operations

- Container runtime includes healthcheck and hardened Python defaults (`PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`)
- CI hardening checks include:
	- repository secret scan (`gitleaks`)
	- dependency vulnerability scan (`pip-audit`)
	- dependency license policy scan (`scripts/check_licenses.py`)
	- containerized smoke E2E (`scripts/container-smoke-e2e.sh`)
- Operations runbook: `docs/runbook-operations.md`
