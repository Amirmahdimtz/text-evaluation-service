"""Atomic PostgreSQL SKIP LOCKED claims and fenced heartbeat."""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select, update

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import Evaluation, EvaluationJob
from src.infrastructure.repositories.base.base_repository import BaseRepository


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
