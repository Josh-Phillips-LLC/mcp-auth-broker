from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .secrets import SecretProvider, SecretProviderError, SecretReference


@dataclass(frozen=True)
class TokenRecord:
    access_token: str
    token_type: str
    expires_at_epoch: float
    source: str


@dataclass(frozen=True)
class TokenResult:
    token: str
    metadata: dict[str, object]


class GraphTokenProviderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class GraphTokenMintClient(Protocol):
    def mint(
        self,
        *,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
        timeout_seconds: int,
    ) -> tuple[str, str, int]: ...


class GraphTokenCache:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str, tuple[str, ...]], TokenRecord] = {}

    def get_valid(
        self,
        *,
        key: tuple[str, str, tuple[str, ...]],
        now_epoch: float,
        skew_seconds: int,
    ) -> TokenRecord | None:
        record = self._records.get(key)
        if record is None:
            return None
        if record.expires_at_epoch <= now_epoch + skew_seconds:
            return None
        return record

    def put(
        self,
        *,
        key: tuple[str, str, tuple[str, ...]],
        access_token: str,
        token_type: str,
        expires_in_seconds: int,
        now_epoch: float,
        max_ttl_seconds: int,
    ) -> TokenRecord:
        effective_ttl = max(1, min(expires_in_seconds, max_ttl_seconds))
        record = TokenRecord(
            access_token=access_token,
            token_type=token_type,
            expires_at_epoch=now_epoch + effective_ttl,
            source="minted",
        )
        self._records[key] = record
        return record


class HttpGraphTokenMintClient:
    def mint(
        self,
        *,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
        timeout_seconds: int,
    ) -> tuple[str, str, int]:
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        body = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            token_url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise GraphTokenProviderError("provider.timeout", "token provider timeout") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise GraphTokenProviderError(
                    "provider.auth_failed", "token provider auth failed"
                ) from exc
            if exc.code == 429:
                raise GraphTokenProviderError(
                    "provider.rate_limited", "token provider rate limited"
                ) from exc
            raise GraphTokenProviderError(
                "provider.unavailable", "token provider unavailable"
            ) from exc
        except urllib.error.URLError as exc:
            raise GraphTokenProviderError(
                "provider.unavailable", "token provider unavailable"
            ) from exc

        try:
            access_token = str(payload["access_token"])
            token_type = str(payload.get("token_type", "Bearer"))
            expires_in = int(payload["expires_in"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GraphTokenProviderError(
                "provider.bad_response", "token provider bad response"
            ) from exc

        return access_token, token_type, expires_in


class GraphTokenProvider:
    def __init__(
        self,
        *,
        client_id: str,
        secret_reference: SecretReference,
        secret_provider: SecretProvider,
        mint_client: GraphTokenMintClient | None = None,
        cache: GraphTokenCache | None = None,
        allowed_resources: tuple[str, ...] = ("https://graph.microsoft.com",),
        allowed_scopes: tuple[str, ...] = ("User.Read",),
        cache_skew_seconds: int = 60,
        max_ttl_seconds: int = 3000,
        timeout_seconds: int = 4,
    ) -> None:
        self.client_id = client_id
        self.secret_reference = secret_reference
        self.secret_provider = secret_provider
        self.mint_client = mint_client or HttpGraphTokenMintClient()
        self.cache = cache or GraphTokenCache()
        self.allowed_resources = allowed_resources
        self.allowed_scopes = allowed_scopes
        self.cache_skew_seconds = cache_skew_seconds
        self.max_ttl_seconds = max_ttl_seconds
        self.timeout_seconds = timeout_seconds

    def get_token(
        self,
        *,
        tenant_id: str,
        resource: str,
        scopes: list[str],
        force_refresh: bool = False,
        now_epoch: float | None = None,
    ) -> TokenResult:
        now = now_epoch if now_epoch is not None else time.time()
        self._validate_allowlist(resource=resource, scopes=scopes)

        key = (tenant_id, self.client_id, tuple(scopes))
        if not force_refresh:
            cached = self.cache.get_valid(
                key=key, now_epoch=now, skew_seconds=self.cache_skew_seconds
            )
            if cached is not None:
                return self._to_result(
                    TokenRecord(
                        access_token=cached.access_token,
                        token_type=cached.token_type,
                        expires_at_epoch=cached.expires_at_epoch,
                        source="cache",
                    ),
                    tenant_id=tenant_id,
                    resource=resource,
                    scopes=scopes,
                )

        try:
            client_secret = self.secret_provider.resolve(self.secret_reference)
            access_token, token_type, expires_in = self.mint_client.mint(
                tenant_id=tenant_id,
                client_id=self.client_id,
                client_secret=client_secret,
                scope=" ".join(scopes),
                timeout_seconds=self.timeout_seconds,
            )
            minted = self.cache.put(
                key=key,
                access_token=access_token,
                token_type=token_type,
                expires_in_seconds=expires_in,
                now_epoch=now,
                max_ttl_seconds=self.max_ttl_seconds,
            )
            return self._to_result(minted, tenant_id=tenant_id, resource=resource, scopes=scopes)
        except SecretProviderError as exc:
            raise GraphTokenProviderError(exc.code, exc.message) from exc
        except GraphTokenProviderError as exc:
            fallback = self.cache.get_valid(
                key=key, now_epoch=now, skew_seconds=self.cache_skew_seconds
            )
            if fallback is not None:
                return self._to_result(
                    TokenRecord(
                        access_token=fallback.access_token,
                        token_type=fallback.token_type,
                        expires_at_epoch=fallback.expires_at_epoch,
                        source="cache_fallback",
                    ),
                    tenant_id=tenant_id,
                    resource=resource,
                    scopes=scopes,
                )
            raise exc

    def _validate_allowlist(self, *, resource: str, scopes: list[str]) -> None:
        if resource not in self.allowed_resources:
            raise GraphTokenProviderError(
                "policy.denied",
                "provider resource is not allowlisted",
            )

        disallowed_scopes = [scope for scope in scopes if scope not in self.allowed_scopes]
        if disallowed_scopes:
            raise GraphTokenProviderError(
                "policy.invalid_scope", "requested scope is not allowlisted"
            )

    def _to_result(
        self,
        record: TokenRecord,
        *,
        tenant_id: str,
        resource: str,
        scopes: list[str],
    ) -> TokenResult:
        return TokenResult(
            token=record.access_token,
            metadata={
                "tenant_id": tenant_id,
                "resource": resource,
                "scopes": scopes,
                "token_type": record.token_type,
                "expires_at_epoch": int(record.expires_at_epoch),
                "source": record.source,
            },
        )
