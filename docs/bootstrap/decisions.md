# Bootstrap Decisions (Issue #8)

## Scope and Objective

This document establishes the runtime, scaffolding, and CI baseline required by issue #8 and unblocks M0 (#3).

## Decision Summary

1. **Runtime and language**: Python 3.12 is the baseline runtime.
2. **Package management**: `pip` is the baseline package manager.
3. **Repository scaffolding**: `src/` layout for implementation code and `tests/` for unit tests.
4. **Quality baseline**: formatting and linting via `ruff`; unit testing via `pytest`.
5. **CI baseline**: on pushes/PRs to `main`, enforce format check, lint, unit tests, and container build.
6. **Container baseline**: Docker image builds from `python:3.12-slim` and executes a basic module entrypoint.

## Module Layout Convention

- `src/mcp_auth_broker/`: production package modules.
- `tests/`: unit tests only (no integration or provider-specific auth tests in bootstrap).
- `pyproject.toml`: runtime + pinned dev dependency definitions.
- `.github/workflows/ci.yml`: baseline automation.

## Unblock Condition for M0 (#3)

M0 can begin when this baseline is merged to `main` and the CI workflow is green.
