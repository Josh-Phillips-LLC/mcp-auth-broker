from mcp_auth_broker.graph_tokens import GraphTokenCache
from mcp_auth_broker.graph_tokens import GraphTokenProvider
from mcp_auth_broker.graph_tokens import GraphTokenProviderError
from mcp_auth_broker.secrets import SecretReference


class _FakeSecretProvider:
    def __init__(self, secret: str = "secret") -> None:
        self.secret = secret

    def resolve(self, reference: SecretReference) -> str:
        return self.secret


class _MintClientOk:
    def __init__(self) -> None:
        self.calls = 0

    def mint(self, *, tenant_id, client_id, client_secret, scope, timeout_seconds):
        self.calls += 1
        return "token-abc", "Bearer", 3600


class _MintClientFail:
    def __init__(self, code: str = "provider.unavailable", message: str = "failed") -> None:
        self.code = code
        self.message = message

    def mint(self, *, tenant_id, client_id, client_secret, scope, timeout_seconds):
        raise GraphTokenProviderError(self.code, self.message)


def _provider(mint_client):
    return GraphTokenProvider(
        client_id="client-1",
        secret_reference=SecretReference.parse("op://vault/item/field"),
        secret_provider=_FakeSecretProvider(),
        mint_client=mint_client,
        cache=GraphTokenCache(),
        allowed_resources=("https://graph.microsoft.com",),
        allowed_scopes=("User.Read",),
        cache_skew_seconds=60,
        max_ttl_seconds=3000,
    )


def test_graph_token_happy_path_and_cache_hit():
    mint_client = _MintClientOk()
    provider = _provider(mint_client)

    first = provider.get_token(
        tenant_id="tenant-1",
        resource="https://graph.microsoft.com",
        scopes=["User.Read"],
        now_epoch=1000,
    )
    second = provider.get_token(
        tenant_id="tenant-1",
        resource="https://graph.microsoft.com",
        scopes=["User.Read"],
        now_epoch=1010,
    )

    assert first.metadata["source"] == "minted"
    assert second.metadata["source"] == "cache"
    assert mint_client.calls == 1


def test_graph_token_enforces_provider_allowlist():
    provider = _provider(_MintClientOk())

    try:
        provider.get_token(
            tenant_id="tenant-1",
            resource="https://example.com",
            scopes=["User.Read"],
            now_epoch=1000,
        )
    except GraphTokenProviderError as exc:
        assert exc.code == "policy.denied"
    else:
        raise AssertionError("expected provider allowlist denial")


def test_graph_token_enforces_scope_allowlist():
    provider = _provider(_MintClientOk())

    try:
        provider.get_token(
            tenant_id="tenant-1",
            resource="https://graph.microsoft.com",
            scopes=["Mail.Read"],
            now_epoch=1000,
        )
    except GraphTokenProviderError as exc:
        assert exc.code == "policy.invalid_scope"
    else:
        raise AssertionError("expected scope allowlist denial")


def test_graph_token_cache_applies_ttl_clamp():
    mint_client = _MintClientOk()
    provider = GraphTokenProvider(
        client_id="client-1",
        secret_reference=SecretReference.parse("op://vault/item/field"),
        secret_provider=_FakeSecretProvider(),
        mint_client=mint_client,
        cache=GraphTokenCache(),
        allowed_resources=("https://graph.microsoft.com",),
        allowed_scopes=("User.Read",),
        cache_skew_seconds=60,
        max_ttl_seconds=120,
    )

    token = provider.get_token(
        tenant_id="tenant-1",
        resource="https://graph.microsoft.com",
        scopes=["User.Read"],
        now_epoch=1000,
    )

    assert token.metadata["expires_at_epoch"] == 1120


def test_refresh_failure_returns_valid_cached_fallback():
    mint_client = _MintClientOk()
    provider = _provider(mint_client)

    provider.get_token(
        tenant_id="tenant-1",
        resource="https://graph.microsoft.com",
        scopes=["User.Read"],
        now_epoch=1000,
    )
    provider.mint_client = _MintClientFail(code="provider.unavailable", message="down")

    fallback = provider.get_token(
        tenant_id="tenant-1",
        resource="https://graph.microsoft.com",
        scopes=["User.Read"],
        force_refresh=True,
        now_epoch=1010,
    )

    assert fallback.metadata["source"] == "cache_fallback"


def test_refresh_failure_does_not_return_expired_token():
    mint_client = _MintClientOk()
    provider = _provider(mint_client)

    provider.get_token(
        tenant_id="tenant-1",
        resource="https://graph.microsoft.com",
        scopes=["User.Read"],
        now_epoch=1000,
    )
    provider.mint_client = _MintClientFail(code="provider.unavailable", message="down")

    try:
        provider.get_token(
            tenant_id="tenant-1",
            resource="https://graph.microsoft.com",
            scopes=["User.Read"],
            force_refresh=True,
            now_epoch=5000,
        )
    except GraphTokenProviderError as exc:
        assert exc.code == "provider.unavailable"
    else:
        raise AssertionError("expected deterministic provider failure for expired cache")
