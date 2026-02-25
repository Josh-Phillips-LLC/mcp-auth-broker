from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import BrokerConfig


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    reason: str
    metadata: dict[str, Any]


def evaluate_policy(request: dict[str, Any], config: BrokerConfig) -> PolicyDecision:
    requester = request.get("requester") or {}
    requester_id = requester.get("requester_id")
    if not requester_id:
        return PolicyDecision(
            decision="deny",
            reason="policy.missing_identity",
            metadata={
                "policy_version": config.policy_version,
                "matched_rule_id": None,
                "requester_id": "",
                "tenant_id": _tenant_id(request),
                "scopes_evaluated": _requested_scopes(request),
            },
        )

    scopes = _requested_scopes(request)
    unsupported_scopes = [scope for scope in scopes if scope not in config.allowed_scopes]
    if unsupported_scopes:
        return PolicyDecision(
            decision="deny",
            reason="policy.rule.deny.scope.not_permitted",
            metadata={
                "policy_version": config.policy_version,
                "matched_rule_id": None,
                "requester_id": requester_id,
                "tenant_id": _tenant_id(request),
                "scopes_evaluated": scopes,
            },
        )

    return PolicyDecision(
        decision="allow",
        reason="policy.rule.allow.graph.user.read",
        metadata={
            "policy_version": config.policy_version,
            "matched_rule_id": "allow-user-read",
            "requester_id": requester_id,
            "tenant_id": _tenant_id(request),
            "scopes_evaluated": scopes,
        },
    )


def _tenant_id(request: dict[str, Any]) -> str:
    graph = request.get("graph") or {}
    return str(graph.get("tenant_id") or "")


def _requested_scopes(request: dict[str, Any]) -> list[str]:
    graph = request.get("graph") or {}
    scopes = graph.get("scopes")
    if isinstance(scopes, list):
        return [str(scope) for scope in scopes]
    return []
