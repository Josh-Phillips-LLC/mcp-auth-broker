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
