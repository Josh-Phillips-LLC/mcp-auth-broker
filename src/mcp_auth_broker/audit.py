from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import BrokerConfig


@dataclass
class AuditEmitter:
    emit_to_stdout: bool = True
    events: list[dict[str, Any]] = field(default_factory=list)

    def emit(
        self,
        *,
        config: BrokerConfig,
        event_type: str,
        request: dict[str, Any],
        trace_id: str,
        payload: dict[str, Any],
        redactions: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        requester = request.get("requester") or {}
        event = {
            "schema_version": config.contract_version,
            "event_type": event_type,
            "event_id": str(uuid4()),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "request_id": request.get("request_id", ""),
            "trace_id": trace_id,
            "requester_id": requester.get("requester_id", ""),
            "service": config.service_name,
            "environment": config.environment,
            "redactions": redactions or [],
            "payload": payload,
        }
        self.events.append(event)
        if self.emit_to_stdout:
            print(json.dumps(event, sort_keys=True))
        return event
