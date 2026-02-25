# ADR-0003: Token Handling Policy

- ADR ID: `ADR-0003`
- Status: `Accepted`
- Date: `2026-02-25`
- Owner: `@joshphillipssr`

## Context

M0 must decide whether broker tools return raw tokens to callers or execute downstream provider calls directly and return only downstream results.

## Options Considered

1. Return raw access token to caller
2. Broker executes downstream call and never returns token
3. Hybrid mode with configurable token return

## Selected Option

Use **broker-executed downstream call only** for phase 1 and do not return raw tokens.

## Trade-offs

- Benefits:
  - Reduces token exfiltration risk.
  - Simplifies redact-by-default guarantees.
  - Aligns auditing to full request-to-result flow in one service.
- Costs:
  - Broker must support operation envelope for downstream call execution.
  - Some client patterns expecting direct token use require adaptation.

## Rejection Rationale

- Option 1 rejected due to higher exposure risk and downstream misuse potential.
- Option 3 rejected because policy branching increases early-phase complexity and drift risk.

## Rollback / Revisit Trigger

Revisit if a validated use case requires controlled token return with strong attestation, scoped audiences, and explicit compensating controls.
