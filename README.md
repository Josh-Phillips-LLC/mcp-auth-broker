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
