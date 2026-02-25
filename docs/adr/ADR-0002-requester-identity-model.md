# ADR-0002: Initial Requester Identity Signal

- ADR ID: `ADR-0002`
- Status: `Accepted`
- Date: `2026-02-25`
- Owner: `@joshphillipssr`

## Context

Policy evaluation requires requester identity at decision time. M0 must define a minimal initial identity signal that does not require a full identity platform build.

## Options Considered

1. Unauthenticated caller-provided requester ID
2. Trusted upstream asserted requester ID (broker trusts authenticated transport boundary)
3. Broker-verified signed identity token (JWT) in phase 1

## Selected Option

Use **trusted upstream asserted requester ID** in phase 1.

## Trade-offs

- Benefits:
  - Minimal implementation complexity for M0/M1.
  - Enables deterministic policy decisions and auditing now.
  - Defers token verification subsystem complexity to a later phase.
- Costs:
  - Security posture depends on correctness of upstream trust boundary.
  - Requires clear deployment guidance for trusted channels.

## Rejection Rationale

- Option 1 rejected due to spoofing risk and weak assurance.
- Option 3 rejected for phase 1 due to added key management and token validation complexity.

## Rollback / Revisit Trigger

Revisit when multi-tenant or external caller scenarios require broker-side identity verification guarantees beyond trusted upstream assertion.
