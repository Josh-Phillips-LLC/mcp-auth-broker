# Non-Functional Contracts (M0)

## Version

- Non-functional contract version: `v0.1.0`

## Versioning and Compatibility

- Patch updates (`v0.1.x`) may adjust narrative clarifications and non-breaking defaults.
- Minor updates (`v0.x.0`) may tighten operational targets where backward compatible.
- Breaking runtime expectation changes require a new major version and explicit rollout plan.

## Timeout Expectations

- End-to-end request timeout default: `10000ms`.
- Secret retrieval timeout per attempt: `1500ms`.
- Token mint/provider auth timeout per attempt: `3000ms`.
- Provider downstream call timeout per attempt: `4000ms`.

If budget is exhausted, return deterministic timeout code (`secret.timeout` or `provider.timeout`).

## Retry Expectations

- Secret retrieval retries: up to `2` retries (max `3` total attempts), exponential backoff (`100ms`, `250ms`).
- Token mint/provider auth retries: up to `1` retry (max `2` total attempts), backoff `200ms`.
- No retries for policy-denied or bad-request errors.

## Audit Sink and Retention (Phase 1)

- Sink mode: structured JSON events to stdout.
- Centralized sink: not required in phase 1.
- Local retention expectation: platform log retention policy applies; broker does not persist local audit files.
- Minimum retention target for centralized follow-on phase: 30 days (decision checkpoint for M1/M2).

## Reliability and Safety Baseline

- All responses and events are redact-by-default.
- Token material is never returned in tool responses.
- Errors are deterministic and category-coded for implementer and client handling.

## Revisit Triggers

- Any provider latency profile violating timeout budget in >5% of requests.
- Compliance requirement introducing mandatory centralized audit retention.
- New provider integration requiring different retry/timeout tuning.
