"""Real Stage09 PostgreSQL lease/recovery tests: isolated synthetic DB only."""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from src.core.services.text_evaluation.evaluation_worker_service import (
    EvaluationWorkerService, WorkerPolicy, WorkerResult, WorkerRetryableError,
)
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext, get_test_database_url
from src.infrastructure.models.text_evaluation import (
    AuditEvent, CriterionResult, Evaluation, EvaluationJob, RubricVersion,
)
from src.infrastructure.repositories.text_evaluation.evaluation_repository import EvaluationRepository
from src.infrastructure.repositories.text_evaluation.evaluation_job_repository import EvaluationJobRepository


@pytest.fixture(scope="module", autouse=True)
def isolated_stage09_schema():
    if not os.getenv("TES_STAGE05_DATABASE_URL"):
        pytest.skip("PENDING_LOCAL_DB: isolated PostgreSQL URL not provided")
    pytest.importorskip("asyncpg")
    get_test_database_url()
    from alembic import command
    from alembic.config import Config
    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[1] / "src/infrastructure/alembic"),
    )
    command.upgrade(config, "head")
    return config


def config(*, max_attempts=3, max_inflight=2, max_queue_depth=8):
    return WorkerPolicy(
        lease_seconds=2, heartbeat_seconds=0.05,
        execution_timeout_seconds=0.4,
        max_attempts=max_attempts, retry_base_seconds=0,
        retry_cap_seconds=0, max_inflight=max_inflight,
        max_queue_depth=max_queue_depth, poll_seconds=0.01,
        recovery_batch_size=50, drain_seconds=0.1,
    )


async def seed(ctx, *, organization_id=None, owner="synthetic-owner"):
    org = organization_id or ("stage09-org-" + uuid4().hex)
    rubric_id = uuid4()
    async with ctx.session() as session:
        async with session.begin():
            session.add(RubricVersion(
                id=rubric_id, organization_id=org, evaluation_type="speech",
                code="synthetic-stage09", version="candidate-test",
                status="published", criteria_snapshot={"criteria": []},
                checksum="a" * 64, published_at=datetime.now(timezone.utc),
            ))
    evaluation_id, job_id = uuid4(), uuid4()
    await EvaluationRepository(ctx).create_with_job_async(
        Evaluation(
            id=evaluation_id, organization_id=org, owner_id=owner,
            evaluation_type="speech", rubric_version_id=rubric_id,
            protected_text_ref=uuid4(), idempotency_key=uuid4().hex,
            request_fingerprint="b" * 64,
        ),
        EvaluationJob(
            id=job_id, evaluation_id=evaluation_id, organization_id=org,
        ),
        organization_id=org, owner_id=owner, correlation_id=uuid4(),
    )
    return org, evaluation_id, job_id


def fixture_result(ctx):
    return WorkerResult(
        criterion_results=(CriterionResult(
            id=uuid4(), evaluation_id=ctx.evaluation_id,
            organization_id=ctx.organization_id,
            criterion_code="speech_clarity", status="assessed",
            score=4, encrypted_details=b"SYNTHETIC_TEST_ONLY_CIPHERTEXT",
        ),),
        coverage=0.65, model_revision="synthetic-model",
        prompt_version="synthetic-prompt", result_status="needs_human_review",
    )


def test_real_db_concurrent_claim_crash_recovery_and_stale_fencing(isolated_stage09_schema):
    async def exercise():
        db = PsqlDbContext()
        try:
            org, evaluation_id, job_id = await seed(db)
            jobs = EvaluationJobRepository(db)
            evals = EvaluationRepository(db)
            async def claim(worker):
                return await jobs.claim_next_async(
                    organization_id=org, worker_id=worker,
                    lease_duration=timedelta(seconds=60), max_attempts=3,
                )
            first = await asyncio.gather(claim("worker-A"), claim("worker-B"))
            winner = [j for j in first if j is not None]
            assert len(winner) == 1
            old = winner[0]
            assert old.attempts == 1
            assert old.fencing_generation == 1
            # Simulate process crash by expiring lease in this ISOLATED test DB.
            async with db.session() as session:
                async with session.begin():
                    await session.execute(text(
                        "UPDATE evaluation_jobs SET lease_until=clock_timestamp() "
                        "- interval '1 second' WHERE id=:job_id"
                    ), {"job_id": job_id})
            assert await jobs.recover_expired_async(
                organization_id=org, max_attempts=3, retry_delay=timedelta(0),
            ) == 1
            assert not await jobs.heartbeat_async(
                organization_id=org, job_id=job_id,
                worker_id=old.worker_id, attempt_token=old.attempt_token,
                fencing_generation=old.fencing_generation,
                lease_duration=timedelta(seconds=60),
            )
            assert not await evals.finalize_with_results_async(
                organization_id=org, owner_id="synthetic-owner",
                evaluation_id=evaluation_id, job_id=job_id,
                worker_id=old.worker_id, attempt_token=old.attempt_token,
                fencing_generation=old.fencing_generation,
                results=list(fixture_result(type(
                    "Context", (), {"evaluation_id": evaluation_id, "organization_id": org},
                )()).criterion_results),
                overall_score=None, coverage=0.65,
                model_revision="synthetic-model", prompt_version="synthetic-prompt",
                correlation_id=uuid4(), result_status="needs_human_review",
            )
            next_job = await claim("worker-C")
            assert next_job is not None and next_job.attempts == 2
            assert next_job.fencing_generation > old.fencing_generation
            assert next_job.attempt_token != old.attempt_token
            assert not await jobs.fail_attempt_async(
                organization_id=org, job_id=job_id, worker_id=old.worker_id,
                attempt_token=old.attempt_token,
                fencing_generation=old.fencing_generation,
                max_attempts=3, retryable=True, error_code="INFERENCE_TIMEOUT",
                retry_delay=timedelta(0),
            )

            # Live worker never holds a Session or Transaction while executor waits.
            async def authorized_synthetic_executor(ctx):
                assert db._engine.sync_engine.pool.checkedout() == 0
                await asyncio.sleep(0.02)
                assert db._engine.sync_engine.pool.checkedout() == 0
                return fixture_result(ctx)

            # The already claimed attempt can be completed with fencing fields.
            token = next_job.attempt_token
            ctx = await evals.worker_context_async(
                organization_id=org, job_id=job_id, worker_id="worker-C",
                attempt_token=token,
                fencing_generation=next_job.fencing_generation,
            )
            assert ctx is not None and ctx.protected_text_ref is not None
            result = await authorized_synthetic_executor(ctx)
            assert await evals.finalize_with_results_async(
                organization_id=org, owner_id=ctx.owner_id,
                evaluation_id=ctx.evaluation_id, job_id=job_id,
                worker_id="worker-C", attempt_token=token,
                fencing_generation=next_job.fencing_generation,
                results=list(result.criterion_results),
                overall_score=None, coverage=result.coverage,
                model_revision=result.model_revision, prompt_version=result.prompt_version,
                correlation_id=uuid4(), result_status=result.result_status,
            )
            assert not await claim("worker-D")
            async with db.session() as session:
                job = await session.get(EvaluationJob, job_id)
                evaluation = await session.get(Evaluation, evaluation_id)
                assert job.status == "completed" and job.worker_id is None
                assert evaluation.status == "needs_human_review"
                assert evaluation.overall_score is None
                assert evaluation.coverage == 0.65
                assert (await session.scalar(
                    select(func.count()).select_from(CriterionResult).where(
                        CriterionResult.evaluation_id == evaluation_id,
                    )
                )) == 1
            assert db._engine.sync_engine.pool.checkedout() == 0
        finally:
            await db.close()
    asyncio.run(exercise())


def test_real_db_worker_service_retry_then_terminal_and_queue_metrics(isolated_stage09_schema):
    async def exercise():
        db = PsqlDbContext()
        try:
            org, evaluation_id, job_id = await seed(db)
            job_repo = EvaluationJobRepository(db)
            service = EvaluationWorkerService(job_repo, EvaluationRepository(db))
            p = config(max_attempts=2, max_queue_depth=1)
            assert not await service.can_accept_async(organization_id=org, policy=p)
            initial = await service.metrics_async(organization_id=org)
            assert initial.ready == 1 and initial.processing == 0
            seen = []
            async def bad_executor(ctx):
                assert db._engine.sync_engine.pool.checkedout() == 0
                seen.append(ctx.evaluation_id)
                raise WorkerRetryableError("sensitive exception never stored")
            assert await service.process_once_async(
                organization_id=org, worker_id="worker-one", policy=p,
                executor=bad_executor,
            ) == "retry_scheduled"
            after_retry = await service.metrics_async(organization_id=org)
            assert after_retry.ready == 1 and after_retry.retries == 0
            assert await service.process_once_async(
                organization_id=org, worker_id="worker-two", policy=p,
                executor=bad_executor,
            ) == "terminal"
            after = await service.metrics_async(organization_id=org)
            assert after.terminal == 1 and after.ready == 0
            assert seen == [evaluation_id, evaluation_id]
            assert await service.process_once_async(
                organization_id=org, worker_id="worker-three",
                policy=p, executor=bad_executor,
            ) == "idle"
            async with db.session() as session:
                job = await session.get(EvaluationJob, job_id)
                evaluation = await session.get(Evaluation, evaluation_id)
                assert job.attempts == 2
                assert job.status == evaluation.status == "failed_terminal"
                assert job.error_code == "RESOURCE_UNAVAILABLE"
                assert job.attempt_token is None and job.lease_until is None
            assert db._engine.sync_engine.pool.checkedout() == 0
        finally:
            await db.close()
    asyncio.run(exercise())


def test_real_db_max_attempts_expired_lease_becomes_poison_terminal(isolated_stage09_schema):
    async def exercise():
        db = PsqlDbContext()
        try:
            org, eval_id, job_id = await seed(db)
            repo = EvaluationJobRepository(db)
            claimed = await repo.claim_next_async(
                organization_id=org, worker_id="crashed",
                lease_duration=timedelta(seconds=5), max_attempts=1,
            )
            assert claimed is not None
            async with db.session() as session:
                async with session.begin():
                    await session.execute(text(
                        "UPDATE evaluation_jobs SET lease_until=clock_timestamp() "
                        "- interval '1 second' WHERE id=:job_id"
                    ), {"job_id": job_id})
            assert await repo.recover_expired_async(
                organization_id=org, max_attempts=1, retry_delay=timedelta(0),
            ) == 1
            assert await repo.recover_expired_async(
                organization_id=org, max_attempts=1, retry_delay=timedelta(0),
            ) == 0
            async with db.session() as session:
                j = await session.get(EvaluationJob, job_id)
                e = await session.get(Evaluation, eval_id)
                assert j.status == e.status == "failed_terminal"
                assert j.error_code == "LEASE_EXPIRED"
                assert j.fencing_generation >= 2
            assert await repo.claim_next_async(
                organization_id=org, worker_id="new-worker",
                lease_duration=timedelta(seconds=3), max_attempts=1,
            ) is None
        finally:
            await db.close()
    asyncio.run(exercise())
