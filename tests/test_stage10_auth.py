"""Stage10 offline authentication, crypto, DTO, route discovery and deny-by-default."""
from __future__ import annotations

import base64
import os
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import ValidationError

from src.application.text_evaluation.dtos.text_evaluation_dto import (
    CreateEvaluationDto, CreateFeedbackDto, EvaluationResponseDto,
)
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.di.inject import resolve
from src.infrastructure.utils.config_reader import ConfigReader
from src.infrastructure.security.encrypted_content import EncryptedContentService
from src.infrastructure.security.signed_identity import (
    SignedIdentityVerifier, AuthenticationError,
)
from src.host.app import create_app


@pytest.fixture
def signed_env(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
    monkeypatch.setenv("TES_STAGE10_TEST_PUBLIC", public)
    monkeypatch.setenv("TES_STAGE10_TEST_CIPHER", base64.b64encode(os.urandom(32)).decode())
    cfg = resolve(ConfigReader)
    settings = cfg.settings.http_security.__class__.model_validate({
        "enabled": True, "issuer": "synthetic-internal-issuer",
        "audience": "synthetic-text-service",
        "public_key_ref": "env://TES_STAGE10_TEST_PUBLIC",
        "encryption_key_ref": "env://TES_STAGE10_TEST_CIPHER",
        "key_id": "synthetic-key-v1",
        "max_request_bytes": 16384, "max_text_characters": 8192,
        "max_active_jobs": 8, "max_requests_per_minute": 100,
    })
    monkeypatch.setattr(cfg, "settings", cfg.settings.model_copy(update={"http_security": settings}))
    return key


def signed_token(key, **overrides):
    import time
    now = int(time.time())
    claims = {
        "sub": "synthetic-user", "org": "synthetic-org",
        "iss": "synthetic-internal-issuer", "aud": "synthetic-text-service",
        "iat": now, "nbf": now, "exp": now + 600, "jti": uuid4().hex,
        "permissions": ["evaluation:submit", "evaluation:read"],
        "assigned_resource_ids": [],
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def test_stage10_controller_discovered_once_and_prefix_is_exact():
    bootstrap_di()
    app = create_app()
    paths = {r.path for r in app.routes}
    assert {
        "/api/v1/text_evaluation/evaluations",
        "/api/v1/text_evaluation/evaluations/{evaluation_id}",
        "/api/v1/text_evaluation/rubrics",
        "/api/v1/text_evaluation/evaluations/{evaluation_id}/feedback",
    } <= paths
    assert not any("/text_evaluation/text_evaluation" in p for p in paths)
    schema = app.openapi()
    assert schema["paths"]["/api/v1/text_evaluation/evaluations"]["post"]["responses"]["202"]
    assert "CreateEvaluationDto" in schema["components"]["schemas"]


def test_stage10_disabled_by_default_fails_closed_without_key_or_database():
    bootstrap_di()
    cfg = resolve(ConfigReader)
    assert cfg.settings.http_security.enabled is False
    with pytest.raises(AuthenticationError):
        resolve(SignedIdentityVerifier).verify("fake")


def test_stage10_rs256_signature_tamper_and_expiration(signed_env):
    service = resolve(SignedIdentityVerifier)
    token = signed_token(signed_env)
    identity = service.verify(token)
    assert identity.user_id == "synthetic-user"
    assert identity.organization_id == "synthetic-org"
    assert "evaluation:submit" in identity.permissions
    with pytest.raises(AuthenticationError):
        service.verify(token[:-2] + "ab")
    with pytest.raises(AuthenticationError):
        service.verify(signed_token(signed_env, exp=1))
    with pytest.raises(AuthenticationError):
        service.verify(signed_token(signed_env, org=""))
    with pytest.raises(AuthenticationError):
        service.verify(signed_token(signed_env, permissions=["rubric:manage", "unknown:scope"]))
    with pytest.raises(AuthenticationError):
        service.verify(jwt.encode({"sub": "forged"}, "not-an-rsa-key", algorithm="HS256"))


def test_stage10_authenticated_encryption_bound_to_org_owner_id_and_type(signed_env):
    crypto = resolve(EncryptedContentService)
    resource = uuid4()
    data = "متن محرمانه مصنوعی با نیم‌فاصله 🌱"
    ciphertext = crypto.encrypt(
        value=data, organization_id="synthetic-org", owner_id="synthetic-user",
        resource_id=resource, kind="original",
    )
    assert data.encode("utf-8") not in ciphertext
    assert ciphertext != crypto.encrypt(
        value=data, organization_id="synthetic-org", owner_id="synthetic-user",
        resource_id=resource, kind="original",
    )
    assert crypto.decrypt(
        ciphertext=ciphertext, organization_id="synthetic-org",
        owner_id="synthetic-user", resource_id=resource, kind="original",
    ) == data
    for org, owner, ref, kind in [
        ("other-org", "synthetic-user", resource, "original"),
        ("synthetic-org", "other-user", resource, "original"),
        ("synthetic-org", "synthetic-user", uuid4(), "original"),
        ("synthetic-org", "synthetic-user", resource, "feedback"),
    ]:
        with pytest.raises(ValueError, match="ENCRYPTION_INTEGRITY_FAILED"):
            crypto.decrypt(
                ciphertext=ciphertext, organization_id=org,
                owner_id=owner, resource_id=ref, kind=kind,
            )
    corrupted = bytearray(ciphertext)
    corrupted[-1] ^= 1
    with pytest.raises(ValueError, match="ENCRYPTION_INTEGRITY_FAILED"):
        crypto.decrypt(
            ciphertext=bytes(corrupted), organization_id="synthetic-org",
            owner_id="synthetic-user", resource_id=resource, kind="original",
        )


@pytest.mark.parametrize("data", [
    {"text": "", "evaluation_type": "speech", "rubric_code": "speech_quality",
     "rubric_version": "candidate-0.1"},
    {"text": "hello", "evaluation_type": "invalid", "rubric_code": "speech_quality",
     "rubric_version": "candidate-0.1"},
    {"text": "hello", "evaluation_type": "speech", "rubric_code": "../path",
     "rubric_version": "candidate-0.1"},
    {"text": "hello", "evaluation_type": "speech", "rubric_code": "speech_quality",
     "rubric_version": "candidate-0.1", "secret": "not-allowed"},
])
def test_stage10_input_dto_fail_closed(data):
    with pytest.raises(ValidationError):
        CreateEvaluationDto.model_validate(data)


def test_stage10_feedback_only_comment_no_official_approval():
    with pytest.raises(ValidationError):
        CreateFeedbackDto.model_validate({"comment": "approve", "decision_code": "APPROVE"})
    with pytest.raises(ValidationError):
        CreateFeedbackDto.model_validate({"comment": " "})
