# Tool Contracts (M0)

## Version

- Contract set version: `v0.1.0`
- Status: Draft for implementation handoff to M1

## Scope

This document defines canonical request/response contracts for the phase-1 Graph token path.

## Contract Rules

1. Every request must include `contract_version`.
2. Every response must include `contract_version`, `status`, and `request_id`.
3. Unknown request fields are rejected with `bad_request.invalid_field`.
4. Sensitive fields are redacted by default in all responses.

## Tool: `auth.graph.token.acquire.v1`

Purpose: evaluate policy and, if allowed, acquire a Microsoft Graph access token for broker-managed downstream execution.

### Request Schema

```json
{
  "contract_version": "v0.1.0",
  "request_id": "string-uuid",
  "requester": {
    "requester_id": "string",
    "identity_assurance": "asserted|verified"
  },
  "graph": {
    "tenant_id": "string",
    "resource": "https://graph.microsoft.com",
    "scopes": ["User.Read"]
  },
  "operation": {
    "action": "downstream_call",
    "method": "GET|POST|PATCH|DELETE",
    "path": "/v1.0/me",
    "headers": {},
    "body": null
  },
  "timeout_ms": 10000
}
```

### Success Response Schema

```json
{
  "contract_version": "v0.1.0",
  "request_id": "string-uuid",
  "status": "ok",
  "result": {
    "policy": {
      "decision": "allow",
      "reason": "policy.rule.allow.graph.user.read",
      "metadata": {
        "matched_rule_id": "string",
        "policy_version": "string"
      }
    },
    "execution": {
      "mode": "broker_downstream_execution",
      "provider": "microsoft_graph",
      "provider_request_id": "string",
      "http_status": 200,
      "response_headers": {},
      "response_body": {}
    },
    "redactions": []
  }
}
```

### Error Response Schema

```json
{
  "contract_version": "v0.1.0",
  "request_id": "string-uuid",
  "status": "error",
  "error": {
    "code": "policy.denied",
    "message": "Access denied by policy",
    "retryable": false,
    "category": "policy|provider|secret|request",
    "metadata": {
      "decision_id": "string"
    }
  },
  "redactions": [
    {
      "field": "error.metadata.provider_body",
      "reason": "sensitive"
    }
  ]
}
```

## Deterministic Error Taxonomy

### Policy Errors

- `policy.denied`
- `policy.missing_identity`
- `policy.invalid_scope`

### Secret Retrieval Errors

- `secret.not_found`
- `secret.access_denied`
- `secret.timeout`
- `secret.unavailable`

### Provider Errors

- `provider.auth_failed`
- `provider.rate_limited`
- `provider.timeout`
- `provider.unavailable`
- `provider.bad_response`

### Request Errors

- `bad_request.invalid_field`
- `bad_request.invalid_timeout`
- `bad_request.unsupported_operation`

## Redact-by-Default Rules

1. Never return raw access tokens in response payloads.
2. Remove or mask secrets, authorization headers, cookies, and provider credential material.
3. Error metadata may include identifiers and class labels, but not raw secret/provider payloads.
4. Redactions must be enumerated in `redactions` for deterministic client handling.
