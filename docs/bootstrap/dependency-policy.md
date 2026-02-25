# Dependency Policy (Bootstrap)

## Baseline Rules

- Development and quality-tool dependencies are pinned in `requirements-dev.txt`.
- Runtime dependencies are declared in `pyproject.toml`.
- Any new dependency must include a rationale in the PR description.

## Update Cadence

- Review and update dependency pins monthly.
- Apply urgent security updates outside cadence when advisories are published.

## License Guardrails

- Allowed licenses: permissive OSS licenses (MIT, BSD, Apache-2.0).
- Disallowed by default: copyleft dependencies unless explicitly approved.
- PRs adding dependencies must document the package license.
