# ADR-0001: 1Password Phase-1 Integration Mode

- ADR ID: `ADR-0001`
- Status: `Accepted`
- Date: `2026-02-25`
- Owner: `@joshphillipssr`

## Context

M0 requires a phase-1 secret retrieval mode that is implementable quickly without introducing interactive login dependencies in broker runtime.

## Options Considered

1. 1Password CLI with interactive human sign-in session
2. 1Password Service Account token-based machine access
3. 1Password Connect server deployment in phase 1

## Selected Option

Use **1Password Service Account token-based machine access** for phase 1.

## Trade-offs

- Benefits:
  - Non-interactive broker execution path.
  - Lower operational overhead than introducing Connect in phase 1.
  - Fast bootstrap with deterministic runtime behavior.
- Costs:
  - Service account scope management must be tightly controlled.
  - Potential future migration path if Connect is required for enterprise controls.

## Rejection Rationale

- Option 1 rejected due to interactive dependency and poor automation fit.
- Option 3 rejected for phase 1 due to additional infrastructure and rollout complexity.

## Rollback / Revisit Trigger

Revisit if compliance, tenancy isolation, or secret access controls require Connect deployment, or if service account limitations block required use cases.
