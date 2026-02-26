from __future__ import annotations

import os
from dataclasses import dataclass

from .secrets import SecretReference


@dataclass(frozen=True)
class BrokerConfig:
    environment: str
    service_name: str
    contract_version: str
    policy_version: str
    default_timeout_ms: int
    allowed_scopes: tuple[str, ...]
    secret_provider_mode: str
    graph_secret_reference: SecretReference | None
    graph_client_id: str
    allowed_graph_resources: tuple[str, ...]
    token_cache_skew_seconds: int
    token_max_ttl_seconds: int
    token_provider_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "BrokerConfig":
        timeout_raw = os.getenv("MCP_AUTH_BROKER_DEFAULT_TIMEOUT_MS", "10000")
        try:
            timeout_ms = int(timeout_raw)
        except ValueError as exc:
            raise ValueError("MCP_AUTH_BROKER_DEFAULT_TIMEOUT_MS must be an integer") from exc

        if timeout_ms <= 0:
            raise ValueError("MCP_AUTH_BROKER_DEFAULT_TIMEOUT_MS must be positive")

        scopes_raw = os.getenv("MCP_AUTH_BROKER_ALLOWED_SCOPES", "User.Read")
        scopes = tuple(scope.strip() for scope in scopes_raw.split(",") if scope.strip())
        if not scopes:
            raise ValueError("MCP_AUTH_BROKER_ALLOWED_SCOPES must contain at least one scope")

        secret_provider_mode = os.getenv("MCP_AUTH_BROKER_SECRET_PROVIDER", "none")
        if secret_provider_mode not in {"none", "1password"}:
            raise ValueError("MCP_AUTH_BROKER_SECRET_PROVIDER must be one of: none, 1password")

        secret_reference_raw = os.getenv("MCP_AUTH_BROKER_GRAPH_SECRET_REF", "").strip()
        secret_reference = None
        if secret_reference_raw:
            try:
                secret_reference = SecretReference.parse(secret_reference_raw)
            except Exception as exc:
                raise ValueError("MCP_AUTH_BROKER_GRAPH_SECRET_REF is invalid") from exc

        graph_client_id = os.getenv("MCP_AUTH_BROKER_GRAPH_CLIENT_ID", "").strip()

        resources_raw = os.getenv(
            "MCP_AUTH_BROKER_ALLOWED_GRAPH_RESOURCES", "https://graph.microsoft.com"
        )
        allowed_graph_resources = tuple(
            resource.strip() for resource in resources_raw.split(",") if resource.strip()
        )
        if not allowed_graph_resources:
            raise ValueError(
                "MCP_AUTH_BROKER_ALLOWED_GRAPH_RESOURCES must contain at least one value"
            )

        skew_raw = os.getenv("MCP_AUTH_BROKER_TOKEN_CACHE_SKEW_SECONDS", "60")
        ttl_raw = os.getenv("MCP_AUTH_BROKER_TOKEN_MAX_TTL_SECONDS", "3000")
        timeout_raw = os.getenv("MCP_AUTH_BROKER_TOKEN_PROVIDER_TIMEOUT_SECONDS", "4")
        try:
            token_cache_skew_seconds = int(skew_raw)
            token_max_ttl_seconds = int(ttl_raw)
            token_provider_timeout_seconds = int(timeout_raw)
        except ValueError as exc:
            raise ValueError("Token provider/cache settings must be integers") from exc

        if token_cache_skew_seconds < 0:
            raise ValueError("MCP_AUTH_BROKER_TOKEN_CACHE_SKEW_SECONDS cannot be negative")
        if token_max_ttl_seconds <= 0:
            raise ValueError("MCP_AUTH_BROKER_TOKEN_MAX_TTL_SECONDS must be positive")
        if token_provider_timeout_seconds <= 0:
            raise ValueError("MCP_AUTH_BROKER_TOKEN_PROVIDER_TIMEOUT_SECONDS must be positive")

        return cls(
            environment=os.getenv("MCP_AUTH_BROKER_ENV", "dev"),
            service_name=os.getenv("MCP_AUTH_BROKER_SERVICE_NAME", "mcp-auth-broker"),
            contract_version=os.getenv("MCP_AUTH_BROKER_CONTRACT_VERSION", "v0.1.0"),
            policy_version=os.getenv("MCP_AUTH_BROKER_POLICY_VERSION", "v0.1.0"),
            default_timeout_ms=timeout_ms,
            allowed_scopes=scopes,
            secret_provider_mode=secret_provider_mode,
            graph_secret_reference=secret_reference,
            graph_client_id=graph_client_id,
            allowed_graph_resources=allowed_graph_resources,
            token_cache_skew_seconds=token_cache_skew_seconds,
            token_max_ttl_seconds=token_max_ttl_seconds,
            token_provider_timeout_seconds=token_provider_timeout_seconds,
        )
