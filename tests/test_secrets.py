import subprocess

import pytest

from mcp_auth_broker.config import BrokerConfig
from mcp_auth_broker.secrets import OnePasswordSecretProvider, SecretProviderError, SecretReference


class _Completed:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_secret_reference_parse_success():
    ref = SecretReference.parse("op://vault-a/item-b/field-c")
    assert ref.vault == "vault-a"
    assert ref.item == "item-b"
    assert ref.field == "field-c"
    assert ref.to_uri() == "op://vault-a/item-b/field-c"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "vault/item/field",
        "op://vault/item",
        "op:///item/field",
        "op://vault//field",
    ],
)
def test_secret_reference_parse_invalid(value: str):
    with pytest.raises(SecretProviderError):
        SecretReference.parse(value)


def test_config_parses_secret_reference_from_env(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_BROKER_SECRET_PROVIDER", "1password")
    monkeypatch.setenv("MCP_AUTH_BROKER_GRAPH_SECRET_REF", "op://vault/item/field")
    config = BrokerConfig.from_env()
    assert config.secret_provider_mode == "1password"
    assert config.graph_secret_reference is not None
    assert config.graph_secret_reference.to_uri() == "op://vault/item/field"


def test_1password_provider_maps_not_found(monkeypatch):
    provider = OnePasswordSecretProvider(token="token")

    def _fake_run(*args, **kwargs):
        return _Completed(returncode=1, stderr="item not found")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    with pytest.raises(SecretProviderError) as exc:
        provider.resolve(SecretReference.parse("op://vault/item/field"))

    assert exc.value.code == "secret.not_found"


def test_1password_provider_maps_access_denied(monkeypatch):
    provider = OnePasswordSecretProvider(token="token")

    def _fake_run(*args, **kwargs):
        return _Completed(returncode=1, stderr="forbidden")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    with pytest.raises(SecretProviderError) as exc:
        provider.resolve(SecretReference.parse("op://vault/item/field"))

    assert exc.value.code == "secret.access_denied"


def test_1password_provider_maps_timeout(monkeypatch):
    provider = OnePasswordSecretProvider(token="token")

    def _fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["op"], timeout=5)

    monkeypatch.setattr(subprocess, "run", _fake_run)

    with pytest.raises(SecretProviderError) as exc:
        provider.resolve(SecretReference.parse("op://vault/item/field"))

    assert exc.value.code == "secret.timeout"


def test_1password_provider_maps_unavailable_binary(monkeypatch):
    provider = OnePasswordSecretProvider(token="token")

    def _fake_run(*args, **kwargs):
        raise FileNotFoundError("op not found")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    with pytest.raises(SecretProviderError) as exc:
        provider.resolve(SecretReference.parse("op://vault/item/field"))

    assert exc.value.code == "secret.unavailable"
