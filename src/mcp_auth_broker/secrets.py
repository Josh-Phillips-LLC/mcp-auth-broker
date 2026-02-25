from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Protocol


class SecretProviderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SecretReference:
    vault: str
    item: str
    field: str

    @classmethod
    def parse(cls, value: str) -> "SecretReference":
        if not value.startswith("op://"):
            raise SecretProviderError(
                code="bad_request.invalid_field",
                message="secret reference must start with op://",
            )

        parts = value[len("op://"):].split("/")
        if len(parts) != 3 or not all(parts):
            raise SecretProviderError(
                code="bad_request.invalid_field",
                message="secret reference must follow op://vault/item/field",
            )

        return cls(vault=parts[0], item=parts[1], field=parts[2])

    def to_uri(self) -> str:
        return f"op://{self.vault}/{self.item}/{self.field}"


class SecretProvider(Protocol):
    def resolve(self, reference: SecretReference) -> str:
        ...


class OnePasswordSecretProvider:
    def __init__(self, token: str | None = None, op_binary: str = "op") -> None:
        self.token = token or os.getenv("OP_SERVICE_ACCOUNT_TOKEN", "")
        self.op_binary = op_binary

    def resolve(self, reference: SecretReference) -> str:
        if not self.token:
            raise SecretProviderError(
                code="secret.access_denied",
                message="OP_SERVICE_ACCOUNT_TOKEN is required",
            )

        env = dict(os.environ)
        env["OP_SERVICE_ACCOUNT_TOKEN"] = self.token

        try:
            completed = subprocess.run(
                [self.op_binary, "read", reference.to_uri()],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                timeout=5,
            )
        except subprocess.TimeoutExpired as exc:
            raise SecretProviderError(
                code="secret.timeout",
                message="secret provider timed out",
            ) from exc
        except FileNotFoundError as exc:
            raise SecretProviderError(
                code="secret.unavailable",
                message="1Password CLI is not available",
            ) from exc

        if completed.returncode == 0:
            return completed.stdout.strip()

        stderr = (completed.stderr or "").lower()
        if "not found" in stderr:
            raise SecretProviderError(
                code="secret.not_found",
                message="secret reference not found",
            )
        if "forbidden" in stderr or "access denied" in stderr or "unauthorized" in stderr:
            raise SecretProviderError(
                code="secret.access_denied",
                message="secret access denied",
            )

        raise SecretProviderError(
            code="secret.unavailable",
            message="secret provider unavailable",
        )
