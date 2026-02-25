from mcp_auth_broker import MCPAuthBrokerServer, main
from mcp_auth_broker.audit import AuditEmitter
from mcp_auth_broker.config import BrokerConfig
from mcp_auth_broker.server import TOOL_NAME


def _config() -> BrokerConfig:
    return BrokerConfig(
        environment="test",
        service_name="mcp-auth-broker",
        contract_version="v0.1.0",
        policy_version="v0.1.0",
        default_timeout_ms=10000,
        allowed_scopes=("User.Read",),
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
