from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .audit import AuditEmitter
from .config import BrokerConfig
from .policy import evaluate_policy
from .secrets import OnePasswordSecretProvider, SecretProvider, SecretProviderError

TOOL_NAME = "auth.graph.operation.execute.v1"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


class MCPAuthBrokerServer:
    def __init__(
        self,
        config: BrokerConfig | None = None,
        audit: AuditEmitter | None = None,
        secret_provider: SecretProvider | None = None,
    ) -> None:
        self.config = config or BrokerConfig.from_env()
        self.audit = audit or AuditEmitter()
        self.secret_provider = secret_provider or self._build_secret_provider()
        self._tools = [
            ToolDefinition(
                name=TOOL_NAME,
                description="Evaluate policy and execute approved Microsoft Graph operation.",
                input_schema={
                    "type": "object",
                    "required": [
                        "contract_version",
                        "request_id",
                        "requester",
                        "graph",
                        "operation",
                    ],
                },
            )
        ]

    def health(self) -> dict[str, str]:
        return {"status": "ok", "service": self.config.service_name}

    def readiness(self) -> dict[str, str]:
        return {"status": "ready", "environment": self.config.environment}

    def discover_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools
        ]

    def execute_tool(self, tool_name: str, request: dict[str, Any]) -> dict[str, Any]:
        request_id = str(request.get("request_id", ""))
        if tool_name != TOOL_NAME:
            return self._error_response(
                request_id=request_id,
                code="bad_request.unsupported_operation",
                message="Unsupported tool name",
                metadata={"tool_name": tool_name},
            )

        validation_error = self._validate_request(request)
        if validation_error is not None:
            return validation_error

        trace_id = str(uuid4())
        self.audit.emit(
            config=self.config,
            event_type="request.received",
            request=request,
            trace_id=trace_id,
            payload={
                "tool_name": tool_name,
                "contract_version": request["contract_version"],
                "tenant_id": request["graph"].get("tenant_id", ""),
                "requested_scopes": request["graph"].get("scopes", []),
            },
        )

        policy_decision = evaluate_policy(request, self.config)
        self.audit.emit(
            config=self.config,
            event_type="policy.decided",
            request=request,
            trace_id=trace_id,
            payload={
                "decision": policy_decision.decision,
                "reason": policy_decision.reason,
                "policy_version": policy_decision.metadata["policy_version"],
                "matched_rule_id": policy_decision.metadata.get("matched_rule_id"),
            },
        )

        if policy_decision.decision == "deny":
            response = self._error_response(
                request_id=request_id,
                code="policy.denied",
                message="Access denied by policy",
                metadata={"reason_code": policy_decision.reason},
            )
            self.audit.emit(
                config=self.config,
                event_type="result.emitted",
                request=request,
                trace_id=trace_id,
                payload={
                    "status": "error",
                    "error_code": response["error"]["code"],
                    "duration_ms": 0,
                },
            )
            return response

        secret_error = self._resolve_graph_secret(request_id=request_id)
        if secret_error is not None:
            self.audit.emit(
                config=self.config,
                event_type="result.emitted",
                request=request,
                trace_id=trace_id,
                payload={"status": "error", "error_code": secret_error["error"]["code"], "duration_ms": 0},
                redactions=[{"field": "error.metadata.secret_value", "reason": "sensitive"}],
            )
            return secret_error

        self.audit.emit(
            config=self.config,
            event_type="provider.called",
            request=request,
            trace_id=trace_id,
            payload={
                "provider": "microsoft_graph",
                "operation": request["operation"],
                "timeout_ms": request.get("timeout_ms", self.config.default_timeout_ms),
                "attempt": 1,
                "outcome": "success",
            },
        )

        response = {
            "contract_version": self.config.contract_version,
            "request_id": request_id,
            "status": "ok",
            "result": {
                "policy": {
                    "decision": policy_decision.decision,
                    "reason": policy_decision.reason,
                    "metadata": policy_decision.metadata,
                },
                "execution": {
                    "mode": "broker_downstream_execution",
                    "provider": "microsoft_graph",
                    "provider_request_id": str(uuid4()),
                    "http_status": 200,
                    "response_headers": {},
                    "response_body": {"ok": True},
                },
                "redactions": [],
            },
        }
        self.audit.emit(
            config=self.config,
            event_type="result.emitted",
            request=request,
            trace_id=trace_id,
            payload={"status": "ok", "error_code": None, "duration_ms": 0},
        )
        return response

    def _validate_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        allowed_top_level_fields = {
            "contract_version",
            "request_id",
            "requester",
            "graph",
            "operation",
            "timeout_ms",
        }
        unknown_fields = sorted(set(request.keys()) - allowed_top_level_fields)
        if unknown_fields:
            return self._error_response(
                request_id=str(request.get("request_id", "")),
                code="bad_request.invalid_field",
                message="Unknown request fields",
                metadata={"fields": unknown_fields},
            )

        required_fields = [
            "contract_version",
            "request_id",
            "requester",
            "graph",
            "operation",
        ]
        missing_fields = [field for field in required_fields if field not in request]
        if missing_fields:
            return self._error_response(
                request_id=str(request.get("request_id", "")),
                code="bad_request.invalid_field",
                message="Missing required fields",
                metadata={"fields": missing_fields},
            )

        if request["contract_version"] != self.config.contract_version:
            return self._error_response(
                request_id=str(request.get("request_id", "")),
                code="bad_request.invalid_field",
                message="Unsupported contract_version",
                metadata={"contract_version": request["contract_version"]},
            )

        timeout = request.get("timeout_ms", self.config.default_timeout_ms)
        if not isinstance(timeout, int) or timeout <= 0:
            return self._error_response(
                request_id=str(request.get("request_id", "")),
                code="bad_request.invalid_timeout",
                message="timeout_ms must be a positive integer",
                metadata={"timeout_ms": timeout},
            )

        return None

    def _error_response(
        self,
        *,
        request_id: str,
        code: str,
        message: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "contract_version": self.config.contract_version,
            "request_id": request_id,
            "status": "error",
            "error": {
                "code": code,
                "message": message,
                "retryable": False,
                "category": code.split(".")[0],
                "metadata": metadata,
            },
            "redactions": [],
        }

    def _build_secret_provider(self) -> SecretProvider | None:
        if self.config.secret_provider_mode == "1password":
            return OnePasswordSecretProvider()
        return None

    def _resolve_graph_secret(self, *, request_id: str) -> dict[str, Any] | None:
        if self.secret_provider is None or self.config.graph_secret_reference is None:
            return None

        try:
            secret_value = self.secret_provider.resolve(self.config.graph_secret_reference)
        except SecretProviderError as exc:
            return self._error_response(
                request_id=request_id,
                code=exc.code,
                message=exc.message,
                metadata={"reference": self.config.graph_secret_reference.to_uri()},
            )

        if not secret_value:
            return self._error_response(
                request_id=request_id,
                code="secret.not_found",
                message="secret reference returned empty value",
                metadata={"reference": self.config.graph_secret_reference.to_uri()},
            )
        return None
