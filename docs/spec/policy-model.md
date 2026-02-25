# Policy Decision Model (M0)

## Version

- Policy model version: `v0.1.0`

## Versioning and Compatibility

- Patch updates (`v0.1.x`) may clarify semantics and add optional metadata fields.
- Minor updates (`v0.x.0`) may add reason codes but must not rename or remove existing stable codes.
- Breaking policy contract changes require a new major version and migration notes.

## Decision Contract

Every policy evaluation must produce the following structure:

```json
{
  "decision": "allow|deny",
  "reason": "string.code",
  "metadata": {
    "policy_version": "string",
    "matched_rule_id": "string|null",
    "requester_id": "string",
    "tenant_id": "string",
    "scopes_evaluated": ["string"]
  }
}
```

## Inputs

- Requester identity (`requester_id`, assurance level)
- Requested provider operation and scopes
- Target tenant/resource context
- Runtime environmental constraints (timeout budget)

## Decision Semantics

- `allow`: request may proceed to provider execution.
- `deny`: request must terminate before provider execution.

## Reason Code Rules

1. Must be deterministic and machine-readable.
2. Must map to one primary category: `policy`, `request`, `secret`, or `provider`.
3. Must be stable across patch releases of the same contract version.

Examples:

- `policy.rule.allow.graph.user.read`
- `policy.rule.deny.scope.not_permitted`
- `policy.rule.deny.identity.untrusted`

## Metadata Requirements

- `policy_version` is required.
- `matched_rule_id` required for `allow`, optional for `deny`.
- `requester_id` required; missing identity yields `policy.missing_identity`.
- `scopes_evaluated` required and must preserve evaluation order.

## Determinism Requirements

- Same normalized input + same policy version must produce the same decision and reason code.
- Policy evaluation must be side-effect free.
- Decision payload must be safe to emit to audit events without additional mutation.
