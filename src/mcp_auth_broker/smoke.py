from __future__ import annotations

from .audit import AuditEmitter
from .config import BrokerConfig
from .graph_tokens import GraphTokenCache
from .graph_tokens import GraphTokenProvider
from .secrets import SecretReference
from .server import MCPAuthBrokerServer
from .server import TOOL_NAME


class _SmokeSecretProvider:
    def resolve(self, reference: SecretReference) -> str:
        return "smoke-secret"


class _SmokeMintClient:
    def mint(self, *, tenant_id, client_id, client_secret, scope, timeout_seconds):
        return "smoke-token-value", "Bearer", 600


def run_smoke_e2e() -> dict[str, object]:
    config = BrokerConfig(
        environment="smoke",
        service_name="mcp-auth-broker",
        contract_version="v0.1.0",
        policy_version="v0.1.0",
        default_timeout_ms=10000,
        allowed_scopes=("User.Read",),
        secret_provider_mode="none",
        graph_secret_reference=SecretReference.parse("op://vault/item/field"),
        graph_client_id="smoke-client",
        allowed_graph_resources=("https://graph.microsoft.com",),
        token_cache_skew_seconds=60,
        token_max_ttl_seconds=3000,
        token_provider_timeout_seconds=4,
    )

    token_provider = GraphTokenProvider(
        client_id="smoke-client",
        secret_reference=SecretReference.parse("op://vault/item/field"),
        secret_provider=_SmokeSecretProvider(),
        mint_client=_SmokeMintClient(),
        cache=GraphTokenCache(),
        allowed_resources=("https://graph.microsoft.com",),
        allowed_scopes=("User.Read",),
        cache_skew_seconds=60,
        max_ttl_seconds=3000,
        timeout_seconds=4,
    )

    server = MCPAuthBrokerServer(
        config=config,
        audit=AuditEmitter(emit_to_stdout=False),
        token_provider=token_provider,
    )
    request = {
        "contract_version": "v0.1.0",
        "request_id": "smoke-req-1",
        "requester": {"requester_id": "smoke-user", "identity_assurance": "verified"},
        "graph": {
            "tenant_id": "smoke-tenant",
            "resource": "https://graph.microsoft.com",
            "scopes": ["User.Read"],
        },
        "operation": {"action": "downstream_call", "method": "GET", "path": "/v1.0/me"},
        "timeout_ms": 1000,
    }

    response = server.execute_tool(TOOL_NAME, request)
    if response.get("status") != "ok":
        raise RuntimeError("smoke e2e failed")

    token_metadata = response["result"]["execution"]["response_body"].get("token_metadata")
    if not token_metadata:
        raise RuntimeError("missing token metadata in smoke response")

    if "token" in response["result"]["execution"]["response_body"]:
        raise RuntimeError("token value leaked in smoke response")

    return {
        "status": "ok",
        "checks": ["request", "policy", "secret", "token_response"],
        "token_source": token_metadata.get("source"),
    }
