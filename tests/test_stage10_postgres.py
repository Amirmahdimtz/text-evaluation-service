"""Isolated PostgreSQL 17 + signed RS256 HTTP E2E with synthetic-only text.

No shared Simorgh DB, production keys, live model, external AI or real identity.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy import func, select

from src.core.services.text_evaluation.rubric_schema import RubricSnapshot
from src.core.services.text_evaluation.evaluation_worker_service import (
    EvaluationWorkerService, WorkerPolicy, WorkerResult,
)
from src.host.app import create_app
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext, get_test_database_url
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.di.inject import resolve
from src.infrastructure.models.text_evaluation import (
    AuditEvent, CriterionResult, Evaluation, EvaluationFeedback,
    EvaluationJob, ProtectedText, RubricVersion,
)
from src.infrastructure.repositories.text_evaluation.evaluation_job_repository import EvaluationJobRepository
from src.infrastructure.repositories.text_evaluation.evaluation_repository import EvaluationRepository
from src.infrastructure.security.encrypted_content import EncryptedContentService
from src.infrastructure.utils.config_reader import ConfigReader

SOURCE = "متن ساختگی امن، فقط برای تست یکپارچه‌سازی. 🌱"
FIXTURES = Path(__file__).parent / "fixtures/stage06_candidate_rubrics.json"


@pytest.fixture(scope="module", autouse=True)
def isolated_stage10_schema():
    if not os.getenv("TES_STAGE05_DATABASE_URL"):
        pytest.skip("PENDING_LOCAL_DB: isolated PostgreSQL URL missing")
    pytest.importorskip("asyncpg")
    get_test_database_url()
    from alembic import command
    from alembic.config import Config
    cfg = Config()
    cfg.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "src/infrastructure/alembic"),
    )
    command.upgrade(cfg, "head")


def setup_auth(monkeypatch, *, requests_per_minute=100, max_active_jobs=6,
               max_request_bytes=4096):
    bootstrap_di()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setenv("TES_STAGE10_TEST_PUBLIC", key.public_key().public_bytes(
        Encoding.PEM, PublicFormat.SubjectPublicKeyInfo,
    ).decode())
    monkeypatch.setenv("TES_STAGE10_TEST_CIPHER", base64.b64encode(os.urandom(32)).decode())
    cfg = resolve(ConfigReader)
    settings = cfg.settings.http_security.__class__.model_validate({
        "enabled": True, "issuer": "isolated-stage10-issuer",
        "audience": "isolated-stage10-service",
        "public_key_ref": "env://TES_STAGE10_TEST_PUBLIC",
        "encryption_key_ref": "env://TES_STAGE10_TEST_CIPHER",
        "key_id": "synthetic-ci-key-v1",
        "max_request_bytes": max_request_bytes,
        "max_text_characters": 2048,
        "max_active_jobs": max_active_jobs,
        "max_requests_per_minute": requests_per_minute,
    })
    monkeypatch.setattr(cfg, "settings", cfg.settings.model_copy(
        update={"http_security": settings},
    ))
    return key


def token(key, org, *, user="synthetic-author", perms=None, assigned=(), **changes):
    now = int(time.time())
    payload = {
        "sub": user, "org": org,
        "iss": "isolated-stage10-issuer", "aud": "isolated-stage10-service",
        "iat": now, "nbf": now, "exp": now + 300, "jti": uuid4().hex,
        "permissions": perms if perms is not None else [
            "evaluation:submit", "evaluation:read",
        ],
        "assigned_resource_ids": [str(x) for x in assigned],
    }
    payload.update(changes)
    return jwt.encode(payload, key, algorithm="RS256")


def headers(bearer, *, key="synthetic-idempotency-001"):
    return {"Authorization": "Bearer " + bearer, "Idempotency-Key": key}


def payload():
    return {
        "text": SOURCE, "evaluation_type": "speech",
        "rubric_code": "speech_quality", "rubric_version": "candidate-0.1",
        "target_audience": "synthetic readers", "purpose": "synthetic integration",
    }


async def seed_rubric(db, org):
    raw = json.loads(FIXTURES.read_text(encoding="utf-8"))["speech"]
    candidate = RubricSnapshot.model_validate(raw)
    rubric_id = uuid4()
    async with db.session() as session:
        async with session.begin():
            session.add(RubricVersion(
                id=rubric_id, organization_id=org, evaluation_type="speech",
                code=candidate.code, version=candidate.version, status="published",
                checksum=candidate.fingerprint(), criteria_snapshot=candidate.canonical_dict(),
                published_at=datetime.now(timezone.utc),
            ))
    return rubric_id


def test_stage10_http_submission_report_feedback_and_tenant_idor(
    isolated_stage10_schema, monkeypatch,
):
    key = setup_auth(monkeypatch)
    org = "synthetic-api-" + uuid4().hex
    outsider = "synthetic-outsider-" + uuid4().hex

    async def exercise():
        db = resolve(PsqlDbContext)
        try:
            rubric_id = await seed_rubric(db, org)
            app = create_app()
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://127.0.0.1:8000",
            ) as client:
                auth = token(key, org)
                other_auth = token(key, outsider)
                route = "/api/v1/text_evaluation"
                missing = await client.get(route + "/rubrics")
                assert missing.status_code == 401
                assert missing.json()["error_code"] == "AUTHENTICATION_REQUIRED"
                assert SOURCE not in str(missing.json())
                fake = await client.get(
                    route + "/rubrics",
                    headers={"Authorization": "Bearer invalid", "X-User": "admin",
                             "X-Org": org},
                )
                assert fake.status_code == 401

                rubrics = await client.get(route + "/rubrics",
                                           headers=headers(auth))
                assert rubrics.status_code == 200, rubrics.text
                assert len(rubrics.json()) == 1
                assert rubrics.json()[0]["approval_status"] == "PROPOSED"
                assert rubrics.json()[0]["rubric_version_id"] == str(rubric_id)

                submit = await client.post(
                    route + "/evaluations", json=payload(), headers=headers(auth),
                )
                assert submit.status_code == 202, submit.text
                body = submit.json()
                evaluation_id = UUID(body["evaluation_id"])
                job_id = UUID(body["job_id"])
                assert body["repeated"] is False
                assert SOURCE not in submit.text
                assert submit.headers["Cache-Control"] == "no-store"
                assert submit.headers.get("X-Correlation-ID")
                replay = await client.post(
                    route + "/evaluations", json=payload(), headers=headers(auth),
                )
                assert replay.status_code == 202, replay.text
                assert replay.json()["repeated"] is True
                assert replay.json()["evaluation_id"] == str(evaluation_id)

                changed = payload()
                changed["text"] = SOURCE + " altered"
                conflict = await client.post(
                    route + "/evaluations", json=changed, headers=headers(auth),
                )
                assert conflict.status_code == 409
                assert conflict.json()["error_code"] == "CONFLICT"
                wrong_tenant = await client.get(
                    route + "/evaluations/" + str(evaluation_id),
                    headers=headers(other_auth),
                )
                assert wrong_tenant.status_code == 404
                assert "evaluation_id" not in str(wrong_tenant.json())
                another_owner = await client.get(
                    route + "/evaluations/" + str(evaluation_id),
                    headers=headers(token(key, org, user="other-person")),
                )
                assert another_owner.status_code == 404
                no_permission = await client.get(
                    route + "/evaluations/" + str(evaluation_id),
                    headers=headers(token(key, org, perms=["evaluation:submit"])),
                )
                assert no_permission.status_code == 403
                assert no_permission.json()["error_code"] == "FORBIDDEN"

                pending = await client.get(
                    route + "/evaluations/" + str(evaluation_id),
                    headers=headers(auth),
                )
                assert pending.status_code == 200, pending.text
                assert pending.json()["status"] == "pending"
                assert pending.json()["criteria"] == []
                assert pending.json()["publishable_as_official_score"] is False

                async with db.session() as session:
                    item = await session.get(ProtectedText, (
                        await session.get(Evaluation, evaluation_id)
                    ).protected_text_ref)
                    assert item is not None
                    assert item.key_id == "synthetic-ci-key-v1"
                    assert SOURCE.encode("utf-8") not in item.ciphertext
                    assert (await session.scalar(select(func.count()).select_from(
                        ProtectedText,
                    ).where(ProtectedText.organization_id == org))) == 1

                # Real Stage09 Worker orchestration and fencing with an injected
                # synthetic authorized executor; no live LLM or protected-text read.
                crypto = resolve(EncryptedContentService)
                async def synthetic_executor(context):
                    assert context.evaluation_id == evaluation_id
                    assert context.job_id == job_id
                    assert context.protected_text_ref is not None
                    assert db._engine.sync_engine.pool.checkedout() == 0
                    detail = json.dumps({
                        "reason": "Synthetic criterion evidence", "strengths": [],
                        "weaknesses": [], "recommendations": [],
                        "evidence": [{"quote": SOURCE[:4], "start_offset": 0, "end_offset": 4}],
                    }, ensure_ascii=False)
                    encrypted = crypto.encrypt(
                        value=detail, organization_id=org,
                        owner_id=context.owner_id, resource_id=evaluation_id,
                        kind="criterion",
                    )
                    return WorkerResult(
                        criterion_results=(CriterionResult(
                            id=uuid4(), evaluation_id=evaluation_id,
                            organization_id=org, criterion_code="speech_clarity",
                            status="assessed", score=4, encrypted_details=encrypted,
                        ),), coverage=0.2,
                        model_revision="synthetic-stub-revision",
                        prompt_version="synthetic-prompt",
                        result_status="needs_human_review",
                    )

                worker = EvaluationWorkerService(
                    EvaluationJobRepository(db), EvaluationRepository(db),
                )
                worker_policy = WorkerPolicy(
                    lease_seconds=10, heartbeat_seconds=0.1,
                    execution_timeout_seconds=3, max_attempts=2,
                    retry_base_seconds=0, retry_cap_seconds=0,
                    max_inflight=1, max_queue_depth=10, poll_seconds=0.01,
                    recovery_batch_size=10, drain_seconds=1,
                )
                assert await worker.process_once_async(
                    organization_id=org, worker_id="isolated-stub-worker",
                    policy=worker_policy, executor=synthetic_executor,
                ) == "completed_review"
                assert await worker.process_once_async(
                    organization_id=org, worker_id="isolated-next-worker",
                    policy=worker_policy, executor=synthetic_executor,
                ) == "idle"

                complete = await client.get(
                    route + "/evaluations/" + str(evaluation_id), headers=headers(auth),
                )
                assert complete.status_code == 200, complete.text
                assert complete.json()["status"] == "needs_human_review"
                assert complete.json()["provisional_score"] is None
                assert complete.json()["criteria"][0]["score"] == 4
                assert complete.json()["criteria"][0]["details"]["reason"] == "Synthetic criterion evidence"
                assert complete.json()["publishable_as_official_score"] is False

                reviewer = token(
                    key, org, user="synthetic-reviewer",
                    perms=["feedback:create", "evaluation:read"],
                    assigned=[evaluation_id],
                )
                denied = await client.post(
                    route + "/evaluations/" + str(evaluation_id) + "/feedback",
                    json={"comment": "Synthetic private review"},
                    headers=headers(token(
                        key, org, user="reviewer-not-assigned",
                        perms=["feedback:create"],
                    )),
                )
                assert denied.status_code == 404
                feedback_uri = route + "/evaluations/" + str(evaluation_id) + "/feedback"
                first = await client.post(
                    feedback_uri, json={"comment": "اولین نظر مصنوعی"},
                    headers=headers(reviewer),
                )
                assert first.status_code == 201, first.text
                assert first.json()["revision"] == 1
                second = await client.post(
                    feedback_uri, json={"comment": "دومین نظر مصنوعی"},
                    headers=headers(reviewer),
                )
                assert second.status_code == 201, second.text
                assert second.json()["revision"] == 2
                read_assigned = await client.get(
                    route + "/evaluations/" + str(evaluation_id),
                    headers=headers(reviewer),
                )
                assert read_assigned.status_code == 200
                async with db.session() as session:
                    feedback = (await session.scalars(select(EvaluationFeedback).where(
                        EvaluationFeedback.evaluation_id == evaluation_id,
                    ).order_by(EvaluationFeedback.revision))).all()
                    assert len(feedback) == 2
                    assert b"\\xd8" != feedback[0].encrypted_details[:1]
                    assert "اولین نظر مصنوعی".encode() not in feedback[0].encrypted_details
                    assert (await session.scalar(select(func.count()).select_from(
                        AuditEvent,
                    ).where(AuditEvent.organization_id == org))) >= 4
        finally:
            await db.close()
    asyncio.run(exercise())


def test_stage10_http_validation_rate_limits_backpressure_and_disabled_security(
    isolated_stage10_schema, monkeypatch,
):
    key = setup_auth(monkeypatch, requests_per_minute=2, max_active_jobs=1,
                     max_request_bytes=1024)
    org = "synthetic-rate-" + uuid4().hex
    async def exercise():
        db = resolve(PsqlDbContext)
        try:
            await seed_rubric(db, org)
            app = create_app()
            route = "/api/v1/text_evaluation"
            auth = token(key, org)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://127.0.0.1:8000",
            ) as client:
                oversized = await client.post(
                    route + "/evaluations", headers=headers(auth),
                    json={**payload(), "text": "x" * 3000},
                )
                assert oversized.status_code == 413, oversized.text
                assert "REQUEST_TOO_LARGE" in oversized.text
                bad_media = await client.post(
                    route + "/evaluations", content=b"<xml/>",
                    headers={**headers(auth), "Content-Type": "application/xml"},
                )
                assert bad_media.status_code == 415
                ambiguous = await client.post(
                    route + "/evaluations",
                    content=b'{"text":"safe","text":"override"}',
                    headers={**headers(auth), "Content-Type": "application/json"},
                )
                assert ambiguous.status_code == 422
                invalid = await client.post(
                    route + "/evaluations",
                    headers=headers(auth, key="invalid"),
                    json=payload(),
                )
                assert invalid.status_code == 422
                first = await client.post(
                    route + "/evaluations", json=payload(),
                    headers=headers(auth, key="synthetic-rate-001"),
                )
                assert first.status_code == 202, first.text
                next_request = await client.post(
                    route + "/evaluations", json=payload(),
                    headers=headers(auth, key="synthetic-rate-002"),
                )
                assert next_request.status_code == 429
                # New user (fresh quota) still hits the shared tenant queue cap.
                fresh_user = token(key, org, user="synthetic-second")
                blocked = await client.post(
                    route + "/evaluations", json=payload(),
                    headers=headers(fresh_user, key="synthetic-rate-003"),
                )
                assert blocked.status_code == 429, blocked.text
                assert SOURCE not in str(blocked.json())
                # Expired signed tokens, even with forged headers, are rejected.
                expired = await client.get(
                    route + "/rubrics", headers={
                        **headers(token(key, org, exp=1)),
                        "X-User": "synthetic-author",
                    },
                )
                assert expired.status_code == 401
                # A real signed token does not bypass missing mandatory policies.
                cfg = resolve(ConfigReader)
                current = cfg.settings.http_security
                monkeypatch.setattr(cfg, "settings", cfg.settings.model_copy(
                    update={"http_security": current.model_copy(
                        update={"max_active_jobs": None},
                    )},
                ))
                unavailable = await client.get(
                    route + "/rubrics",
                    headers=headers(token(key, org, user="synthetic-third")),
                )
                assert unavailable.status_code == 503
                assert unavailable.json()["error_code"] == "SERVICE_UNAVAILABLE"
        finally:
            await db.close()
    asyncio.run(exercise())
