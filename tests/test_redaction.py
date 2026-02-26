from mcp_auth_broker.audit import AuditEmitter
from mcp_auth_broker.config import BrokerConfig
from mcp_auth_broker.redaction import REDACTION_VALUE
from mcp_auth_broker.redaction import redact_payload


def _config() -> BrokerConfig:
    return BrokerConfig(
        environment="test",
        service_name="mcp-auth-broker",
        contract_version="v0.1.0",
        policy_version="v0.1.0",
        default_timeout_ms=10000,
        allowed_scopes=("User.Read",),
        secret_provider_mode="none",
        graph_secret_reference=None,
        graph_client_id="",
        allowed_graph_resources=("https://graph.microsoft.com",),
        token_cache_skew_seconds=60,
        token_max_ttl_seconds=3000,
        token_provider_timeout_seconds=4,
    )


def test_redaction_matrix_masks_sensitive_fields():
    payload = {
        "access_token": "abc",
        "nested": {
            "client_secret": "value",
            "headers": {"authorization": "Bearer token", "accept": "application/json"},
            "items": [{"cookie": "session-cookie"}, {"normal": "ok"}],
        },
    }

    redacted, redactions = redact_payload(payload)

    assert redacted["access_token"] == REDACTION_VALUE
    assert redacted["nested"]["client_secret"] == REDACTION_VALUE
    assert redacted["nested"]["headers"]["authorization"] == REDACTION_VALUE
    assert redacted["nested"]["headers"]["accept"] == "application/json"
    assert redacted["nested"]["items"][0]["cookie"] == REDACTION_VALUE
    assert any(entry["field"] == "access_token" for entry in redactions)
    assert any(entry["field"] == "nested.client_secret" for entry in redactions)


def test_audit_event_payload_is_redacted_by_default():
    emitter = AuditEmitter(emit_to_stdout=False)

    event = emitter.emit(
        config=_config(),
        event_type="provider.called",
        request={"request_id": "req-1", "requester": {"requester_id": "user-1"}},
        trace_id="trace-1",
        payload={"token": "abc", "normal": "value"},
    )

    assert event["payload"]["token"] == REDACTION_VALUE
    assert event["payload"]["normal"] == "value"
    assert any(entry["field"] == "token" for entry in event["redactions"])
