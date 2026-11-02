"""No-network Stage11 isolation preflight: synthetic private config and secrets."""
from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from src.infrastructure.utils.config_reader import ConfigReader
from scripts.verification.stage11_isolated_runtime_preflight import (
    verify_isolated_configuration, main,
)


@pytest.fixture
def isolated_preflight_env(monkeypatch, tmp_path):
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.delenv("TES_STAGE11_SETTINGS_FILE", raising=False)
    source = ConfigReader().settings.model_dump()

    source["worker"].update({
        "enabled": True, "organization_id": "synthetic-preflight-org",
        "lease_seconds": 30.0, "heartbeat_seconds": 5.0,
        "execution_timeout_seconds": 20.0, "max_attempts": 1,
        "retry_base_seconds": 0.0, "retry_cap_seconds": 0.0,
        "max_inflight": 1, "max_queue_depth": 4,
        "poll_seconds": 1.0, "recovery_batch_size": 2, "drain_seconds": 2.0,
    })
    source["llm"].update({
        "enabled": True, "endpoint": "http://127.0.0.1:18090/v1",
        "model_id": "synthetic-model", "model_revision": "synthetic-revision",
        "max_input_characters": 2048, "max_context_tokens": 8192,
        "max_output_tokens": 512, "timeout_seconds": 20.0,
        "max_concurrency": 1, "max_attempts": 1,
        "retry_backoff_seconds": 0.0, "circuit_failures": 1,
        "circuit_reset_seconds": 30.0, "temperature": 0.0,
        "thinking_mode": "runtime_default",
    })
    source["http_security"].update({
        "enabled": True, "issuer": "synthetic-preflight-issuer",
        "audience": "synthetic-preflight-audience",
        "public_key_ref": "env://TES_STAGE11_PREFLIGHT_PUBLIC",
        "encryption_key_ref": "env://TES_STAGE11_PREFLIGHT_AES",
        "key_id": "synthetic-key-id", "max_request_bytes": 4096,
        "max_text_characters": 2048, "max_active_jobs": 8,
        "max_requests_per_minute": 100,
    })
    private = tmp_path / "private-config.yaml"
    private.write_text(yaml.safe_dump(source), encoding="utf-8")
    private.chmod(0o600)
    monkeypatch.setenv("TES_STAGE11_SETTINGS_FILE", str(private))
    monkeypatch.setenv("TES_STAGE05_DATABASE_URL",
                       "postgresql+asyncpg://ci:synthetic@127.0.0.1:5432/tes_stage05_preflight")

    public = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setenv("TES_STAGE11_PREFLIGHT_PUBLIC", public.public_key().public_bytes(
        Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
    ).decode("ascii"))
    monkeypatch.setenv("TES_STAGE11_PREFLIGHT_AES",
                       base64.b64encode(os.urandom(32)).decode("ascii"))
    return source, private


def test_preflight_validates_config_without_network_or_db(monkeypatch, isolated_preflight_env):
    import socket

    monkeypatch.setattr(socket, "create_connection",
                        lambda *_args, **_kw: pytest.fail("Unexpected network connection"))
    result = verify_isolated_configuration()
    assert result["status"] == "CONFIG_VALIDATED_NO_NETWORK"
    assert result["network_calls"] == result["inference_requests"] == result["migrations"] == 0
    assert "synthetic-model" not in str(result)
    assert "synthetic@" not in str(result)


@pytest.mark.parametrize("field, value", [
    ("worker.enabled", False),
    ("llm.enabled", False),
    ("http_security.enabled", False),
    ("worker.max_inflight", 2),
    ("llm.max_concurrency", 2),
    ("llm.max_attempts", 2),
    ("llm.endpoint", "https://8.8.8.8:443/v1"),
    ("llm.endpoint", "http://127.0.0.1:18080/v1"),
    ("http_security.issuer", ""),
])
def test_preflight_rejects_unsafe_settings(monkeypatch, isolated_preflight_env,
                                          field, value):
    source, private = isolated_preflight_env
    section, key = field.split(".")
    source[section][key] = value
    private.write_text(yaml.safe_dump(source), encoding="utf-8")
    private.chmod(0o600)
    with pytest.raises((ValueError, RuntimeError)):
        verify_isolated_configuration()


@pytest.mark.parametrize("bad_dsn", [
    "postgresql+asyncpg://ci:synthetic@192.168.1.2/tes_stage05_preflight",
    "postgresql+asyncpg://ci:synthetic@127.0.0.1/production",
    "sqlite+aiosqlite:///tmp/test.db",
])
def test_preflight_rejects_unsafe_db(monkeypatch, isolated_preflight_env, bad_dsn):
    monkeypatch.setenv("TES_STAGE05_DATABASE_URL", bad_dsn)
    with pytest.raises(ValueError):
        verify_isolated_configuration()


def test_preflight_requires_explicit_private_settings(monkeypatch):
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.delenv("TES_STAGE11_SETTINGS_FILE", raising=False)
    with pytest.raises(ValueError, match="STAGE11_PREFLIGHT_PRIVATE_SETTINGS_REQUIRED"):
        verify_isolated_configuration()


def test_preflight_rejects_bad_aes_key_and_redacts_output(
    monkeypatch, isolated_preflight_env, capsys
):
    monkeypatch.setenv("TES_STAGE11_PREFLIGHT_AES", "synthetic-not-base64")
    assert main() == 2
    output = capsys.readouterr().out
    assert "STAGE11_ISOLATED_CONFIG_INVALID" in output
    assert "synthetic-not-base64" not in output
    assert "synthetic@" not in output
