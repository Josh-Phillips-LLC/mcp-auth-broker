from __future__ import annotations

from typing import Any

REDACTION_VALUE = "***REDACTED***"
SENSITIVE_KEYWORDS = (
    "token",
    "secret",
    "authorization",
    "cookie",
    "password",
    "api_key",
)


def redact_payload(payload: Any) -> tuple[Any, list[dict[str, str]]]:
    redactions: list[dict[str, str]] = []

    def _walk(value: Any, path: str) -> Any:
        if isinstance(value, dict):
            redacted_dict: dict[str, Any] = {}
            for key, item in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                key_lower = str(key).lower()
                if any(keyword in key_lower for keyword in SENSITIVE_KEYWORDS):
                    redactions.append({"field": key_path, "reason": "sensitive"})
                    redacted_dict[key] = REDACTION_VALUE
                else:
                    redacted_dict[key] = _walk(item, key_path)
            return redacted_dict

        if isinstance(value, list):
            return [_walk(item, f"{path}[{index}]") for index, item in enumerate(value)]

        return value

    return _walk(payload, ""), redactions
