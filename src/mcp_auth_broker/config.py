from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BrokerConfig:
    environment: str
    service_name: str
    contract_version: str
    policy_version: str
    default_timeout_ms: int
    allowed_scopes: tuple[str, ...]

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

        return cls(
            environment=os.getenv("MCP_AUTH_BROKER_ENV", "dev"),
            service_name=os.getenv("MCP_AUTH_BROKER_SERVICE_NAME", "mcp-auth-broker"),
            contract_version=os.getenv("MCP_AUTH_BROKER_CONTRACT_VERSION", "v0.1.0"),
            policy_version=os.getenv("MCP_AUTH_BROKER_POLICY_VERSION", "v0.1.0"),
            default_timeout_ms=timeout_ms,
            allowed_scopes=scopes,
        )
