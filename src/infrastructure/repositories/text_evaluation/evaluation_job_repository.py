"""Atomic PostgreSQL SKIP LOCKED claims and fenced heartbeat."""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4
from dataclasses import dataclass

from sqlalchemy import func, or_, select, update

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import AuditEvent, Evaluation, EvaluationJob
from src.infrastructure.repositories.base.base_repository import BaseRepository



@dataclass(frozen=True)
class QueueMetrics:
    ready: int
    delayed: int
    processing: int
    expired_leases: int
    terminal: int
    retries: int
    oldest_ready_age_seconds: float | None


@inject
class EvaluationJobRepository(BaseRepository[EvaluationJob]):
    def __init__(self, db_context: PsqlDbContext) -> None:
        super().__init__(db_context, EvaluationJob)

    async def claim_next_async(
        self, *, organization_id: str, worker_id: str, lease_duration: timedelta, max_attempts: int
    ) -> EvaluationJob | None:
        """Commit claim before any model call. Lease time is policy-injected by caller."""
        self._scope(organization_id)
        if (not worker_id or not isinstance(lease_duration, timedelta) or lease_duration.total_seconds() <= 0
                or type(max_attempts) is not int or not 1 <= max_attempts <= 32767):
            raise ValueError("DB_LEASE_POLICY_REQUIRED")
        async with self._db.session() as session:
            async with session.begin():
                now = await session.scalar(select(func.now()))
                job = (await session.scalars(
                    select(EvaluationJob).where(
                        EvaluationJob.organization_id == organization_id,
                        EvaluationJob.status.in_(("pending", "failed_retryable")),
                        EvaluationJob.attempts < max_attempts,
                        or_(EvaluationJob.retry_after.is_(None), EvaluationJob.retry_after <= now),
                    ).order_by(EvaluationJob.created_at, EvaluationJob.id)
                    .limit(1).with_for_update(skip_locked=True)
                )).one_or_none()
                if job is None:
                    return None
                changed = await session.execute(update(Evaluation).where(
                    Evaluation.id == job.evaluation_id,
                    Evaluation.organization_id == organization_id,
                    Evaluation.status.in_(("pending", "failed_retryable")),
                ).values(status="processing"))
                if changed.rowcount != 1:
                    raise ValueError("DB_CLAIM_STATE_MISMATCH")
                job.status = "processing"
                job.attempts += 1
                job.fencing_generation += 1
                job.attempt_token = uuid4()
                job.worker_id = worker_id
                job.lease_until = now + lease_duration
            return job

    async def heartbeat_async(
        self, *, organization_id: str, job_id: UUID, worker_id: str,
        attempt_token: UUID, fencing_generation: int, lease_duration: timedelta,
    ) -> bool:
        self._scope(organization_id)
        if (not worker_id or not isinstance(attempt_token, UUID)
                or not isinstance(lease_duration, timedelta) or lease_duration.total_seconds() <= 0
                or not isinstance(fencing_generation, int) or fencing_generation < 1):
            raise ValueError("DB_LEASE_POLICY_REQUIRED")
        async with self._db.session() as session:
            async with session.begin():
                now = await session.scalar(select(func.now()))
                updated = await session.execute(update(EvaluationJob).where(
                    EvaluationJob.id == job_id,
                    EvaluationJob.organization_id == organization_id,
                    EvaluationJob.status == "processing",
                    EvaluationJob.worker_id == worker_id,
                    EvaluationJob.attempt_token == attempt_token,
                    EvaluationJob.fencing_generation == fencing_generation,
                    EvaluationJob.lease_until > now,
                ).values(lease_until=now + lease_duration))
                return updated.rowcount == 1

    async def recover_expired_async(
        self, *, organization_id: str, max_attempts: int,
        retry_delay: timedelta, batch_size: int = 100,
    ) -> int:
        """Reclaim after crash by DB clock, invalidate old tokens and record retry/terminal."""
        self._scope(organization_id)
        if (type(max_attempts) is not int or not 1 <= max_attempts <= 32767
                or not isinstance(retry_delay, timedelta) or retry_delay.total_seconds() < 0
                or type(batch_size) is not int or not 1 <= batch_size <= 100):
            raise ValueError("DB_RECOVERY_POLICY_INVALID")
        async with self._db.session() as session:
            async with session.begin():
                now = await session.scalar(select(func.clock_timestamp()))
                expired = (await session.scalars(select(EvaluationJob).where(
                    EvaluationJob.organization_id == organization_id,
                    EvaluationJob.status == "processing",
                    EvaluationJob.lease_until <= now,
                ).order_by(EvaluationJob.lease_until, EvaluationJob.id)
                 .limit(batch_size).with_for_update(skip_locked=True))).all()
                for job in expired:
                    evaluation = (await session.scalars(select(Evaluation).where(
                        Evaluation.id == job.evaluation_id,
                        Evaluation.organization_id == organization_id,
                    ).with_for_update())).one_or_none()
                    if evaluation is None or evaluation.status != "processing":
                        raise ValueError("DB_RECOVERY_STATE_MISMATCH")
                    terminal = job.attempts >= max_attempts
                    next_status = "failed_terminal" if terminal else "failed_retryable"
                    job.status = next_status
                    job.error_code = "LEASE_EXPIRED"
                    job.retry_after = None if terminal else now + retry_delay
                    job.lease_until = None
                    job.worker_id = None
                    job.attempt_token = None
                    job.fencing_generation += 1
                    evaluation.status = next_status
                    session.add(AuditEvent(
                        organization_id=organization_id, actor_id="stage09-recovery",
                        action_code="JOB_LEASE_EXPIRED_TERMINAL" if terminal else "JOB_LEASE_RECOVERED",
                        resource_kind="evaluation", resource_id=job.evaluation_id,
                        correlation_id=uuid4(),
                    ))
            return len(expired)

    async def fail_attempt_async(
        self, *, organization_id: str, job_id: UUID, worker_id: str,
        attempt_token: UUID, fencing_generation: int, max_attempts: int,
        retryable: bool, error_code: str, retry_delay: timedelta,
    ) -> bool:
        """Short fenced transaction; rejected expired/stale worker cannot requeue job."""
        self._scope(organization_id)
        allowed_errors = frozenset({
            "INFERENCE_TIMEOUT", "INFERENCE_TRANSIENT", "INFERENCE_INVALID",
            "EXECUTION_FAILED", "JOB_DEADLINE_EXCEEDED", "RESULT_REJECTED",
            "RESOURCE_UNAVAILABLE", "SHUTDOWN_INTERRUPTED",
        })
        if (not isinstance(job_id, UUID) or not worker_id
                or not isinstance(attempt_token, UUID)
                or type(fencing_generation) is not int or fencing_generation < 1
                or type(max_attempts) is not int or not 1 <= max_attempts <= 32767
                or type(retryable) is not bool or error_code not in allowed_errors
                or not isinstance(retry_delay, timedelta) or retry_delay.total_seconds() < 0):
            raise ValueError("DB_FAILURE_POLICY_INVALID")
        async with self._db.session() as session:
            async with session.begin():
                now = await session.scalar(select(func.clock_timestamp()))
                job = (await session.scalars(select(EvaluationJob).where(
                    EvaluationJob.id == job_id,
                    EvaluationJob.organization_id == organization_id,
                ).with_for_update())).one_or_none()
                if (job is None or job.status != "processing"
                        or job.worker_id != worker_id
                        or job.attempt_token != attempt_token
                        or job.fencing_generation != fencing_generation
                        or job.lease_until is None or job.lease_until <= now):
                    return False
                evaluation = (await session.scalars(select(Evaluation).where(
                    Evaluation.id == job.evaluation_id,
                    Evaluation.organization_id == organization_id,
                    Evaluation.status == "processing",
                ).with_for_update())).one_or_none()
                if evaluation is None:
                    raise ValueError("DB_FAILURE_STATE_MISMATCH")
                terminal = not retryable or job.attempts >= max_attempts
                next_status = "failed_terminal" if terminal else "failed_retryable"
                job.status = next_status
                job.error_code = error_code
                job.retry_after = None if terminal else now + retry_delay
                job.lease_until = None
                job.worker_id = None
                job.attempt_token = None
                job.fencing_generation += 1
                evaluation.status = next_status
                session.add(AuditEvent(
                    organization_id=organization_id, actor_id=worker_id,
                    action_code="JOB_FAILED_TERMINAL" if terminal else "JOB_RETRY_SCHEDULED",
                    resource_kind="evaluation", resource_id=job.evaluation_id,
                    correlation_id=uuid4(),
                ))
            return True

    async def queue_metrics_async(self, *, organization_id: str) -> QueueMetrics:
        """Aggregate only tenant-safe state counts, never raw source or error traces."""
        self._scope(organization_id)
        async with self._db.session() as session:
            now = await session.scalar(select(func.clock_timestamp()))
            jobs = EvaluationJob
            scoped = jobs.organization_id == organization_id
            ready = jobs.status.in_(("pending", "failed_retryable")) & (
                (jobs.retry_after.is_(None)) | (jobs.retry_after <= now)
            )
            delayed = jobs.status == "failed_retryable"
            delayed = delayed & (jobs.retry_after > now)
            row = (await session.execute(select(
                func.count().filter(ready),
                func.count().filter(delayed),
                func.count().filter(jobs.status == "processing"),
                func.count().filter((jobs.status == "processing") & (jobs.lease_until <= now)),
                func.count().filter(jobs.status == "failed_terminal"),
                func.count().filter(jobs.attempts > 1),
                func.min(jobs.created_at).filter(ready),
            ).where(scoped))).one()
            oldest = row[6]
            age = max(0.0, (now - oldest).total_seconds()) if oldest else None
            return QueueMetrics(*(int(row[i]) for i in range(6)), age)
