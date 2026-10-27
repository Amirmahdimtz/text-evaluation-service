"""Real PostgreSQL integration: only local or approved ephemeral synthetic test DB.

Skipped, never PASSED, when TES_STAGE05_DATABASE_URL/asyncpg is absent.
No migrations against shared DB, no test schema teardown or destructive downgrade.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext, get_test_database_url
from src.infrastructure.models.text_evaluation import (
    AuditEvent, CriterionResult, Evaluation, EvaluationFeedback, EvaluationJob, RubricVersion,
)
from src.infrastructure.repositories.text_evaluation.evaluation_repository import EvaluationRepository
from src.infrastructure.repositories.text_evaluation.evaluation_job_repository import EvaluationJobRepository
from src.infrastructure.repositories.text_evaluation.evaluation_feedback_repository import EvaluationFeedbackRepository


@pytest.fixture(scope="module", autouse=True)
def isolated_postgres_schema():
    if not os.getenv("TES_STAGE05_DATABASE_URL"):
        pytest.skip("PENDING_LOCAL_DB: no isolated PostgreSQL test URL")
    pytest.importorskip("asyncpg")
    get_test_database_url()
    from alembic import command
    from alembic.config import Config
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "src/infrastructure/alembic"))
    command.upgrade(config, "head")
    return config


def test_stage05_postgresql_constraints_fencing_and_atomic_transactions(isolated_postgres_schema):
    async def exercise():
        ctx = PsqlDbContext()
        try:
            org = "synthetic-org-" + uuid4().hex
            owner = "synthetic-owner-" + uuid4().hex
            other_org = "synthetic-other-" + uuid4().hex
            rubric_id = uuid4()
            rubric = RubricVersion(
                id=rubric_id, organization_id=org, evaluation_type="speech",
                code="synthetic", version="synthetic-0.1", status="published",
                criteria_snapshot={"criteria": []}, checksum="a" * 64,
                published_at=datetime.now(timezone.utc),
            )
            async with ctx.session() as session:
                async with session.begin():
                    session.add(rubric)
            evrepo = EvaluationRepository(ctx)
            jr = EvaluationJobRepository(ctx)
            eval_id, job_id = uuid4(), uuid4()
            def build_pair(eid, jid):
                return (
                    Evaluation(id=eid, organization_id=org, owner_id=owner,
                               evaluation_type="speech", rubric_version_id=rubric_id,
                               protected_text_ref=uuid4(), idempotency_key="synthetic-"+rubric_id.hex,
                               request_fingerprint="b" * 64, status="pending"),
                    EvaluationJob(id=jid, evaluation_id=eid, organization_id=org, status="pending")
                )

            original = await evrepo.create_with_job_async(
                *build_pair(eval_id, job_id), organization_id=org,
                owner_id=owner, correlation_id=uuid4(),
            )
            assert original == (eval_id, job_id, False)
            replay = await evrepo.create_with_job_async(
                *build_pair(uuid4(), uuid4()), organization_id=org,
                owner_id=owner, correlation_id=uuid4(),
            )
            assert replay == (eval_id, job_id, True)
            with pytest.raises(ValueError, match="DB_IDEMPOTENCY_CONFLICT"):
                a, b = build_pair(uuid4(), uuid4())
                a.request_fingerprint = "c" * 64
                await evrepo.create_with_job_async(
                    a, b, organization_id=org, owner_id=owner,
                    correlation_id=uuid4(),
                )
            assert await evrepo.get_by_id_async(eval_id, organization_id=other_org, owner_id=owner) is None
            assert await evrepo.get_by_id_async(eval_id, organization_id=org, owner_id="unauthorized") is None

            claims = await asyncio.gather(
                jr.claim_next_async(organization_id=org, worker_id="worker-A",
                                    lease_duration=timedelta(seconds=60), max_attempts=3),
                jr.claim_next_async(organization_id=org, worker_id="worker-B",
                                    lease_duration=timedelta(seconds=60), max_attempts=3),
            )
            nonempty = [c for c in claims if c is not None]
            assert len(nonempty) == 1
            claim = nonempty[0]
            assert claim.id == job_id and claim.fencing_generation == 1 and claim.attempts == 1
            assert await jr.heartbeat_async(
                organization_id=org, job_id=job_id, worker_id=claim.worker_id,
                attempt_token=claim.attempt_token, fencing_generation=claim.fencing_generation,
                lease_duration=timedelta(seconds=60),
            )
            assert not await jr.heartbeat_async(
                organization_id=org, job_id=job_id, worker_id=claim.worker_id,
                attempt_token=uuid4(), fencing_generation=claim.fencing_generation,
                lease_duration=timedelta(seconds=60),
            )
            assert not await evrepo.finalize_with_results_async(
                organization_id=org, owner_id=owner, evaluation_id=eval_id,
                job_id=job_id, worker_id=claim.worker_id, attempt_token=uuid4(),
                fencing_generation=claim.fencing_generation,
                results=[CriterionResult(
                    evaluation_id=eval_id, organization_id=org, criterion_code="synthetic",
                    status="assessed", score=4, encrypted_details=b"SYNTHETIC_CIPHER_FIXTURE",
                )], overall_score=80, coverage=1, model_revision="synthetic-model",
                prompt_version="synthetic-prompt", correlation_id=uuid4(),
            )
            result = CriterionResult(
                id=uuid4(), evaluation_id=eval_id, organization_id=org,
                criterion_code="synthetic", status="assessed", score=4,
                encrypted_details=b"SYNTHETIC_CIPHER_FIXTURE",
            )
            assert await evrepo.finalize_with_results_async(
                organization_id=org, owner_id=owner, evaluation_id=eval_id,
                job_id=job_id, worker_id=claim.worker_id, attempt_token=claim.attempt_token,
                fencing_generation=claim.fencing_generation, results=[result],
                overall_score=80, coverage=1, model_revision="synthetic-model",
                prompt_version="synthetic-prompt", correlation_id=uuid4(),
            )
            assert not await evrepo.finalize_with_results_async(
                organization_id=org, owner_id=owner, evaluation_id=eval_id,
                job_id=job_id, worker_id=claim.worker_id, attempt_token=claim.attempt_token,
                fencing_generation=claim.fencing_generation, results=[result],
                overall_score=80, coverage=1, model_revision="synthetic-model",
                prompt_version="synthetic-prompt", correlation_id=uuid4(),
            )
            fb = EvaluationFeedbackRepository(ctx)
            with pytest.raises(ValueError, match="DB_FEEDBACK_NOT_AUTHORIZED"):
                await fb.append_authorized_async(
                    organization_id=org, reviewer_id="reviewer",
                    assigned_evaluation_ids=frozenset(),
                    evaluation_id=eval_id, revision=1, decision_code="reviewed",
                    encrypted_details=b"SYNTHETIC_CIPHER_FIXTURE", correlation_id=uuid4(),
                )
            await fb.append_authorized_async(
                organization_id=org, reviewer_id="reviewer",
                assigned_evaluation_ids=frozenset({eval_id}),
                evaluation_id=eval_id, revision=1, decision_code="reviewed",
                encrypted_details=b"SYNTHETIC_CIPHER_FIXTURE", correlation_id=uuid4(),
            )
            async with ctx.session() as session:
                assert await session.scalar(select(func.count()).select_from(CriterionResult).where(
                    CriterionResult.evaluation_id == eval_id)) == 1
                assert await session.scalar(select(func.count()).select_from(AuditEvent).where(
                    AuditEvent.organization_id == org)) == 3
                assert (await session.scalar(select(Evaluation.status).where(
                    Evaluation.id == eval_id))) == "completed"
            # The published rubric snapshot and append-only feedback are DB protected.
            for forbidden in (
                text("UPDATE rubric_versions SET checksum=:checksum WHERE id=:id"),
                text("DELETE FROM evaluation_feedback WHERE evaluation_id=:id"),
            ):
                with pytest.raises(DBAPIError):
                    async with ctx.session() as session:
                        async with session.begin():
                            await session.execute(forbidden, {"id": rubric_id if "UPDATE" in str(forbidden) else eval_id,
                                                             "checksum": "d" * 64})
        finally:
            await ctx.close()
    asyncio.run(exercise())


def test_stage05_upgrade_is_idempotent_with_existing_synthetic_data(isolated_postgres_schema):
    # Existing synthetic tables/data remain; no destructive downgrade or reset.
    from alembic import command
    command.upgrade(isolated_postgres_schema, "head")
    async def check():
        ctx = PsqlDbContext()
        try:
            async with ctx.session() as session:
                rev = await session.scalar(text("SELECT version_num FROM alembic_version"))
                assert rev == "20261027_05"
        finally:
            await ctx.close()
    asyncio.run(check())
