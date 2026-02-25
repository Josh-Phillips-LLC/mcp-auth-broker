# Audit Event Schema (M0)

## Version

- Audit schema version: `v0.1.0`

## Required Event Types

The schema must represent at minimum these events per request flow:

1. `request.received`
2. `policy.decided`
3. `provider.called`
4. `result.emitted`

## Common Envelope

```json
{
  "schema_version": "v0.1.0",
  "event_type": "request.received",
  "event_id": "string-uuid",
  "occurred_at": "2026-02-25T00:00:00Z",
  "request_id": "string-uuid",
  "trace_id": "string",
  "requester_id": "string",
  "service": "mcp-auth-broker",
  "environment": "dev|staging|prod",
  "redactions": []
}
```

## Event Payload Requirements

### `request.received`

Required payload fields:

- `tool_name`
- `contract_version`
- `tenant_id`
- `requested_scopes`

### `policy.decided`

Required payload fields:

- `decision` (`allow|deny`)
- `reason`
- `policy_version`
- `matched_rule_id` (nullable)

### `provider.called`

Required payload fields:

- `provider` (`microsoft_graph`)
- `operation`
- `timeout_ms`
- `attempt`
- `outcome` (`success|error|timeout`)

### `result.emitted`

Required payload fields:

- `status` (`ok|error`)
- `error_code` (nullable)
- `duration_ms`

## Redaction Rules

- Never write raw bearer tokens or secret values to audit payloads.
- Record redaction entries in `redactions` with `field` and `reason`.
- Provider response bodies are logged only when classified non-sensitive.

## Correlation Rules

- All events for one flow share `request_id`.
- `trace_id` must be stable across request, policy, provider, and result events.
- Event ordering is append-only and timestamped UTC ISO-8601.
