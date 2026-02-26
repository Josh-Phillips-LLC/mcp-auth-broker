from mcp_auth_broker import MCPAuthBrokerServer, main
from mcp_auth_broker.audit import AuditEmitter
from mcp_auth_broker.config import BrokerConfig
from mcp_auth_broker.graph_tokens import GraphTokenProviderError
from mcp_auth_broker.secrets import SecretReference
from mcp_auth_broker.secrets import SecretProviderError
from mcp_auth_broker.server import TOOL_NAME


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


def _allow_request() -> dict:
    return {
        "contract_version": "v0.1.0",
        "request_id": "req-123",
        "requester": {"requester_id": "user-1", "identity_assurance": "verified"},
        "graph": {
            "tenant_id": "tenant-1",
            "resource": "https://graph.microsoft.com",
            "scopes": ["User.Read"],
        },
        "operation": {"action": "downstream_call", "method": "GET", "path": "/v1.0/me"},
        "timeout_ms": 1000,
    }


def test_main_runs(capsys):
    main([])
    captured = capsys.readouterr()
    assert '"status": "started"' in captured.out


def test_tool_discovery_returns_expected_signature():
    server = MCPAuthBrokerServer(config=_config(), audit=AuditEmitter(emit_to_stdout=False))
    tools = server.discover_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == TOOL_NAME
    assert "required" in tools[0]["input_schema"]


def test_allow_path_invokes_policy_and_audit_lifecycle():
    audit = AuditEmitter(emit_to_stdout=False)
    server = MCPAuthBrokerServer(config=_config(), audit=audit)

    response = server.execute_tool(TOOL_NAME, _allow_request())

    assert response["status"] == "ok"
    assert response["result"]["policy"]["decision"] == "allow"
    assert response["result"]["policy"]["reason"] == "policy.rule.allow.graph.user.read"
    assert response["result"]["execution"]["response_body"]["token_metadata"] is None
    assert [event["event_type"] for event in audit.events] == [
        "request.received",
        "policy.decided",
        "provider.called",
        "result.emitted",
    ]


def test_deny_path_returns_stable_reason_code():
    audit = AuditEmitter(emit_to_stdout=False)
    server = MCPAuthBrokerServer(config=_config(), audit=audit)
    request = _allow_request()
    request["graph"]["scopes"] = ["Mail.Read"]

    response = server.execute_tool(TOOL_NAME, request)

    assert response["status"] == "error"
    assert response["error"]["code"] == "policy.denied"
    assert response["error"]["metadata"]["reason_code"] == "policy.rule.deny.scope.not_permitted"
    assert [event["event_type"] for event in audit.events] == [
        "request.received",
        "policy.decided",
        "result.emitted",
    ]


class _FailingSecretProvider:
    def resolve(self, reference):
        raise SecretProviderError(code="secret.access_denied", message="secret access denied")


class _FakeTokenResult:
    def __init__(self):
        self.token = "redacted"
        self.metadata = {
            "tenant_id": "tenant-1",
            "resource": "https://graph.microsoft.com",
            "scopes": ["User.Read"],
            "token_type": "Bearer",
            "expires_at_epoch": 999999,
            "source": "minted",
        }


class _FakeTokenProvider:
    def get_token(self, *, tenant_id, resource, scopes, force_refresh=False, now_epoch=None):
        return _FakeTokenResult()


class _FailingTokenProvider:
    def get_token(self, *, tenant_id, resource, scopes, force_refresh=False, now_epoch=None):
        raise GraphTokenProviderError("provider.unavailable", "token provider unavailable")


def test_secret_provider_failure_returns_deterministic_error_code():
    audit = AuditEmitter(emit_to_stdout=False)
    server = MCPAuthBrokerServer(
        config=BrokerConfig(
            environment="test",
            service_name="mcp-auth-broker",
            contract_version="v0.1.0",
            policy_version="v0.1.0",
            default_timeout_ms=10000,
            allowed_scopes=("User.Read",),
            secret_provider_mode="1password",
            graph_secret_reference=SecretReference.parse("op://vault/item/field"),
            graph_client_id="test-client",
            allowed_graph_resources=("https://graph.microsoft.com",),
            token_cache_skew_seconds=60,
            token_max_ttl_seconds=3000,
            token_provider_timeout_seconds=4,
        ),
        audit=audit,
        secret_provider=_FailingSecretProvider(),
    )

    response = server.execute_tool(TOOL_NAME, _allow_request())

    assert response["status"] == "error"
    assert response["error"]["code"] == "secret.access_denied"
    assert [event["event_type"] for event in audit.events] == [
        "request.received",
        "policy.decided",
        "result.emitted",
    ]


def test_server_returns_token_metadata_without_token_value():
    audit = AuditEmitter(emit_to_stdout=False)
    server = MCPAuthBrokerServer(
        config=_config(),
        audit=audit,
        token_provider=_FakeTokenProvider(),
    )

    response = server.execute_tool(TOOL_NAME, _allow_request())

    assert response["status"] == "ok"
    assert response["result"]["execution"]["response_body"]["token_metadata"]["source"] == "minted"
    assert "token" not in response["result"]["execution"]["response_body"]


def test_server_maps_token_provider_failure_deterministically():
    audit = AuditEmitter(emit_to_stdout=False)
    server = MCPAuthBrokerServer(
        config=_config(),
        audit=audit,
        token_provider=_FailingTokenProvider(),
    )

    response = server.execute_tool(TOOL_NAME, _allow_request())

    assert response["status"] == "error"
    assert response["error"]["code"] == "provider.unavailable"
