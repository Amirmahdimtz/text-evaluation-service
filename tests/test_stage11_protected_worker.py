"""Stage11 protected executor security tests: synthetic data, no network/GPU."""
from __future__ import annotations

import asyncio
import base64
import json
import os
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.core.services.text_evaluation.criterion_evaluation_service import CriterionAssessment
from src.core.services.text_evaluation.evaluation_worker_service import WorkerTerminalError
from src.core.services.text_evaluation.protected_evaluation_executor import ProtectedEvaluationExecutor
from src.core.services.text_evaluation.rubric_schema import RubricSnapshot
from src.infrastructure.repositories.text_evaluation.evaluation_repository import WorkerEvaluationContext
from src.infrastructure.security.encrypted_content import EncryptedContentService
from src.infrastructure.security.secrets import SecretResolver

_SOURCE = "این متن کاملاً ساختگی برای بررسی ایمن است. 🌱"


class FakeMaterialRepository:
    def __init__(self, source, rubric):
        self.source = source
        self.rubric = rubric
        self.lookups = 0

    async def load_protected_worker_material_async(self, *, context):
        self.lookups += 1
        return (self.source, self.rubric) if self.source else None


class FakeEngine:
    def __init__(self):
        self.calls = 0
        self.bad_evidence = False
        self.closed = False

    async def close_async(self):
        self.closed = True

    async def evaluate_async(self, *, original_text, rubric, chunk_char_limit,
                             max_inference_characters):
        self.calls += 1
        assert original_text == _SOURCE
        assert chunk_char_limit == 4096
        assert max_inference_characters == 4096
        self.binding = rubric
        code = rubric.snapshot.criteria[0].criterion_code
        item = CriterionAssessment(
            criterion_code=code, status="assessed", score=4,
            reason="متن ساختگی است.", reason_code=None,
            evidence=((_SOURCE, 0, len(_SOURCE) - (1 if self.bad_evidence else 0)),),
        )
        remaining = tuple(CriterionAssessment(
            criterion_code=c.criterion_code, status="not_assessed", score=None,
            reason="INSUFFICIENT_EVIDENCE", reason_code="INSUFFICIENT_EVIDENCE",
        ) for c in rubric.snapshot.criteria[1:])
        return SimpleNamespace(
            rubric_version_id=rubric.rubric_version_id,
            evaluation_type=rubric.evaluation_type,
            rubric_checksum=rubric.checksum,
            publishable_as_official_score=False,
            result_status="partial",
            criteria=(item, *remaining),
            coverage_fraction=Decimal("0.2"),
            model_revision="unverified-local-revision",
            prompt_version="synthetic-stage11-prompt",
        )


def _fixture(monkeypatch):
    from pathlib import Path

    raw = json.loads((Path(__file__).parent /
        "fixtures/stage06_candidate_rubrics.json").read_text(encoding="utf-8"))["speech"]
    snapshot = RubricSnapshot.model_validate(raw)
    ctx = WorkerEvaluationContext(
        evaluation_id=uuid4(), job_id=uuid4(), organization_id="synthetic-org",
        owner_id="synthetic-owner", evaluation_type="speech",
        rubric_version_id=uuid4(), protected_text_ref=uuid4(),
    )
    http = SimpleNamespace(
        enabled=True, key_id="synthetic-aes-key-v1",
        encryption_key_ref="env://TES_STAGE11_SYNTHETIC_KEY",
    )
    config = SimpleNamespace(
        environment="development",
        settings=SimpleNamespace(
            security=SimpleNamespace(deny_external_egress=True),
            worker=SimpleNamespace(enabled=True, organization_id=ctx.organization_id),
            llm=SimpleNamespace(enabled=True, max_input_characters=4096),
            http_security=http,
        ),
    )
    monkeypatch.setenv("TES_STAGE11_SYNTHETIC_KEY",
                       base64.b64encode(os.urandom(32)).decode("ascii"))
    encryption = EncryptedContentService(config, SecretResolver())
    cipher = encryption.encrypt(
        value=_SOURCE, organization_id=ctx.organization_id,
        owner_id=ctx.owner_id, resource_id=ctx.protected_text_ref, kind="original",
    )
    source = SimpleNamespace(ciphertext=cipher, key_id=http.key_id)
    rubric = SimpleNamespace(
        id=ctx.rubric_version_id, organization_id=ctx.organization_id,
        evaluation_type=ctx.evaluation_type, status="published",
        code=snapshot.code, version=snapshot.version, checksum=snapshot.fingerprint(),
        criteria_snapshot=snapshot.canonical_dict(),
    )
    repo = FakeMaterialRepository(source, rubric)
    engine = FakeEngine()
    executor = ProtectedEvaluationExecutor(repo, engine, encryption, config)
    return ctx, config, repo, engine, encryption, executor


def test_real_encryption_roundtrip_and_provisional_result(monkeypatch):
    ctx, config, repo, engine, encryption, executor = _fixture(monkeypatch)
    outcome = asyncio.run(executor(ctx))
    assert engine.calls == 1 and repo.lookups == 1
    assert outcome.result_status == "partial"
    assert outcome.coverage == 0.2
    assert outcome.model_revision == "unverified-local-revision"
    assert len(outcome.criterion_results) == len(engine.binding.snapshot.criteria)
    assert _SOURCE.encode("utf-8") not in str(outcome).encode("utf-8")
    assert _SOURCE.encode("utf-8") not in repo.source.ciphertext
    assert all(_SOURCE.encode("utf-8") not in row.encrypted_details
               for row in outcome.criterion_results)
    first = outcome.criterion_results[0]
    decoded = json.loads(encryption.decrypt(
        ciphertext=first.encrypted_details,
        organization_id=ctx.organization_id, owner_id=ctx.owner_id,
        resource_id=ctx.evaluation_id, kind="criterion",
    ))
    assert decoded["criterion_code"] == engine.binding.snapshot.criteria[0].criterion_code
    assert decoded["evidence"][0]["quote"] == _SOURCE
    assert decoded["evidence"][0]["end_offset"] == len(_SOURCE)


@pytest.mark.parametrize("field,value", [
    ("environment", "production"),
    ("egress", False),
    ("worker", False),
    ("llm", False),
    ("auth", False),
    ("organization_id", "wrong-org"),
    ("max_input_characters", 1),
])
def test_fail_closed_before_database_or_decryption(monkeypatch, field, value):
    ctx, config, repo, engine, encryption, executor = _fixture(monkeypatch)
    if field == "environment":
        config.environment = value
    elif field == "egress":
        config.settings.security.deny_external_egress = value
    elif field == "worker":
        config.settings.worker.enabled = value
    elif field == "llm":
        config.settings.llm.enabled = value
    elif field == "auth":
        config.settings.http_security.enabled = value
    elif field == "organization_id":
        config.settings.worker.organization_id = value
    else:
        config.settings.llm.max_input_characters = value
    with pytest.raises(WorkerTerminalError):
        asyncio.run(executor(ctx))
    assert repo.lookups == 0 and engine.calls == 0


def test_source_missing_does_not_infer_or_write(monkeypatch):
    ctx, _, repo, engine, _, executor = _fixture(monkeypatch)
    repo.source = None
    with pytest.raises(WorkerTerminalError, match="WORKER_PROTECTED_SOURCE_NOT_FOUND"):
        asyncio.run(executor(ctx))
    assert engine.calls == 0


def test_older_or_wrong_key_is_rejected_without_inference(monkeypatch):
    ctx, _, repo, engine, _, executor = _fixture(monkeypatch)
    repo.source.key_id = "unavailable-old-key"
    with pytest.raises(WorkerTerminalError, match="WORKER_PROTECTED_KEY_UNAVAILABLE"):
        asyncio.run(executor(ctx))
    assert engine.calls == 0


def test_corrupt_rubric_is_not_used_for_model_inference(monkeypatch):
    ctx, _, repo, engine, _, executor = _fixture(monkeypatch)
    repo.rubric.checksum = "0" * 64
    with pytest.raises(ValueError):
        asyncio.run(executor(ctx))
    assert engine.calls == 0


def test_untrusted_quote_offsets_rejected_before_encrypted_result(monkeypatch):
    ctx, _, repo, engine, _, executor = _fixture(monkeypatch)
    engine.bad_evidence = True
    with pytest.raises(WorkerTerminalError, match="WORKER_EVIDENCE_INVALID"):
        asyncio.run(executor(ctx))
    assert engine.calls == 1


def test_cross_resource_decryption_rejected_by_aad(monkeypatch):
    ctx, _, repo, engine, encryption, executor = _fixture(monkeypatch)
    with pytest.raises(ValueError, match="ENCRYPTION_INTEGRITY_FAILED"):
        encryption.decrypt(
            ciphertext=repo.source.ciphertext,
            organization_id=ctx.organization_id, owner_id="different-owner",
            resource_id=ctx.protected_text_ref, kind="original",
        )
    assert engine.calls == 0


def test_incorrect_context_type_rejected_before_repository(monkeypatch):
    ctx, _, repo, engine, encryption, executor = _fixture(monkeypatch)
    with pytest.raises(WorkerTerminalError):
        asyncio.run(executor(SimpleNamespace(organization_id="synthetic-org")))
    assert repo.lookups == 0 and engine.calls == 0



def test_executor_closes_same_engine_inference_client(monkeypatch):
    ctx, _, repo, engine, _, executor = _fixture(monkeypatch)
    asyncio.run(executor.aclose())
    assert engine.closed is True
    assert engine.calls == 0 and repo.lookups == 0
