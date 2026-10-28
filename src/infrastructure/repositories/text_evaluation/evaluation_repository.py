"""Scoped atomic Evaluation/Job submission and fenced result finalization."""

from __future__ import annotations

from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import (
    AuditEvent, CriterionResult, Evaluation, EvaluationJob, RubricVersion, ProtectedText,
)
from src.infrastructure.repositories.base.base_repository import BaseRepository


@dataclass(frozen=True)
class WorkerEvaluationContext:
    evaluation_id: UUID
    job_id: UUID
    organization_id: str
    owner_id: str
    evaluation_type: str
    rubric_version_id: UUID
    protected_text_ref: UUID


@inject
class EvaluationRepository(BaseRepository[Evaluation]):
    def __init__(self, db_context: PsqlDbContext) -> None:
        super().__init__(db_context, Evaluation)

    async def create_with_job_async(
        self, evaluation: Evaluation, job: EvaluationJob, *,
        organization_id: str, owner_id: str, correlation_id: UUID,
        max_active_jobs: int | None = None,
        encrypted_source: bytes | None = None,
        source_key_id: str | None = None,
    ) -> tuple[UUID, UUID, bool]:
        """Committed together; duplicate key returns scoped same-fingerprint prior job."""
        self._scope(organization_id, owner_id)
        if (not isinstance(evaluation, Evaluation) or not isinstance(job, EvaluationJob)
                or evaluation.organization_id != organization_id or evaluation.owner_id != owner_id
                or job.organization_id != organization_id or job.evaluation_id != evaluation.id
                or not isinstance(evaluation.protected_text_ref, UUID)
                or not evaluation.idempotency_key or len(evaluation.request_fingerprint) != 64
                or not isinstance(evaluation.id, UUID) or not isinstance(job.id, UUID)
                or job.status not in (None, "pending")
                or evaluation.status not in (None, "pending")):
            raise ValueError("DB_SUBMISSION_INVALID")
        if encrypted_source is not None and (
            not isinstance(encrypted_source, bytes) or len(encrypted_source) < 30
            or not isinstance(source_key_id, str) or not 1 <= len(source_key_id) <= 128
        ):
            raise ValueError("DB_ENCRYPTED_SOURCE_INVALID")
        evaluation.status = "pending"
        job.status = "pending"
        try:
            async with self._db.session() as session:
                async with session.begin():
                    if max_active_jobs is not None:
                        if (type(max_active_jobs) is not int
                                or not 1 <= max_active_jobs <= 100000):
                            raise ValueError("DB_QUEUE_CAPACITY_INVALID")
                        # Serialize admission for this tenant across ALL worker/
                        # API processes. A hash collision only serializes extra
                        # tenants; it cannot disclose or mix their data.
                        await session.execute(select(func.pg_advisory_xact_lock(
                            func.hashtextextended(organization_id, 9009),
                        )))
                        prior = (await session.scalars(select(Evaluation).where(
                            Evaluation.organization_id == organization_id,
                            Evaluation.owner_id == owner_id,
                            Evaluation.idempotency_key == evaluation.idempotency_key,
                        ))).one_or_none()
                        if prior is not None:
                            if prior.request_fingerprint != evaluation.request_fingerprint:
                                raise ValueError("DB_IDEMPOTENCY_CONFLICT")
                            existing_job_id = (await session.scalars(
                                select(EvaluationJob.id).where(
                                    EvaluationJob.evaluation_id == prior.id,
                                    EvaluationJob.organization_id == organization_id,
                                )
                            )).one_or_none()
                            if existing_job_id is None:
                                raise ValueError("DB_CONSTRAINT_CONFLICT")
                            return prior.id, existing_job_id, True
                        active = await session.scalar(
                            select(func.count()).select_from(EvaluationJob).where(
                                EvaluationJob.organization_id == organization_id,
                                EvaluationJob.status.in_((
                                    "pending", "processing", "failed_retryable",
                                )),
                            )
                        )
                        if active >= max_active_jobs:
                            raise ValueError("DB_QUEUE_CAPACITY_EXCEEDED")
                    rubric = (await session.scalars(select(RubricVersion.id).where(
                        RubricVersion.id == evaluation.rubric_version_id,
                        RubricVersion.organization_id == organization_id,
                        RubricVersion.evaluation_type == evaluation.evaluation_type,
                        RubricVersion.status == "published",
                    ))).one_or_none()
                    if rubric is None:
                        raise ValueError("DB_RUBRIC_NOT_PUBLISHED")
                    if encrypted_source is not None:
                        session.add(ProtectedText(
                            id=evaluation.protected_text_ref,
                            organization_id=organization_id,
                            owner_id=owner_id,
                            key_id=source_key_id,
                            ciphertext=encrypted_source,
                        ))
                    session.add_all([evaluation, job, AuditEvent(
                        organization_id=organization_id, actor_id=owner_id,
                        action_code="EVALUATION_SUBMITTED", resource_kind="evaluation",
                        resource_id=evaluation.id, correlation_id=correlation_id,
                    )])
            return evaluation.id, job.id, False
        except IntegrityError:
            # Never treat an arbitrary FK failure as an idempotency replay.
            async with self._db.session() as session:
                existing = (await session.scalars(select(Evaluation).where(
                    Evaluation.organization_id == organization_id,
                    Evaluation.owner_id == owner_id,
                    Evaluation.idempotency_key == evaluation.idempotency_key,
                ))).one_or_none()
                if existing is None:
                    raise ValueError("DB_CONSTRAINT_CONFLICT") from None
                if existing.request_fingerprint != evaluation.request_fingerprint:
                    raise ValueError("DB_IDEMPOTENCY_CONFLICT")
                saved_job_id = (await session.scalars(select(EvaluationJob.id).where(
                    EvaluationJob.evaluation_id == existing.id,
                    EvaluationJob.organization_id == organization_id,
                ))).one_or_none()
                if saved_job_id is None:
                    raise ValueError("DB_CONSTRAINT_CONFLICT")
                return existing.id, saved_job_id, True

    async def finalize_with_results_async(
        self, *, organization_id: str, owner_id: str,
        evaluation_id: UUID, job_id: UUID, worker_id: str,
        attempt_token: UUID, fencing_generation: int,
        results: list[CriterionResult], overall_score: float | None,
        coverage: float, model_revision: str, prompt_version: str,
        correlation_id: UUID, result_status: str = "completed",
    ) -> bool:
        """Atomic short transaction, never held across an inference call."""
        self._scope(organization_id, owner_id)
        if (not worker_id or not isinstance(attempt_token, UUID)
                or not isinstance(fencing_generation, int) or fencing_generation < 1
                or (overall_score is not None and not 0 <= overall_score <= 100)
                or (result_status == "completed" and overall_score is None)
                or (result_status != "completed" and overall_score is not None)
                or result_status not in ("completed", "partial", "needs_human_review")
                or not 0 <= coverage <= 1
                or not model_revision or not prompt_version
                or not results or any(
                    result.evaluation_id != evaluation_id
                    or result.organization_id != organization_id
                    or not result.encrypted_details for result in results
                )):
            raise ValueError("DB_FINALIZATION_INVALID")
        async with self._db.session() as session:
            async with session.begin():
                # Row locks and database clock prevent stale workers overwriting success.
                job = (await session.scalars(select(EvaluationJob).where(
                    EvaluationJob.id == job_id,
                    EvaluationJob.evaluation_id == evaluation_id,
                    EvaluationJob.organization_id == organization_id,
                ).with_for_update())).one_or_none()
                now = await session.scalar(select(func.now()))
                if (job is None or job.status != "processing"
                        or job.worker_id != worker_id
                        or job.attempt_token != attempt_token
                        or job.fencing_generation != fencing_generation
                        or job.lease_until is None or job.lease_until <= now):
                    return False
                evaluation = (await session.scalars(select(Evaluation).where(
                    Evaluation.id == evaluation_id,
                    Evaluation.organization_id == organization_id,
                    Evaluation.owner_id == owner_id,
                    Evaluation.status == "processing",
                ).with_for_update())).one_or_none()
                if evaluation is None:
                    return False
                for result in results:
                    session.add(result)
                evaluation.status = result_status
                evaluation.overall_score = overall_score
                evaluation.coverage = coverage
                evaluation.model_revision = model_revision
                evaluation.prompt_version = prompt_version
                evaluation.completed_at = now
                job.status = "completed"
                job.lease_until = None
                job.attempt_token = None
                job.worker_id = None
                session.add(AuditEvent(
                    organization_id=organization_id, actor_id=worker_id,
                    action_code="EVALUATION_COMPLETED", resource_kind="evaluation",
                    resource_id=evaluation_id, correlation_id=correlation_id,
                ))
        return True

    async def worker_context_async(
        self, *, organization_id: str, job_id: UUID,
        worker_id: str, attempt_token: UUID, fencing_generation: int,
    ) -> WorkerEvaluationContext | None:
        """Scoped immutable metadata only; never fetch or decrypt confidential text."""
        if (not organization_id or not worker_id or not isinstance(job_id, UUID)
                or not isinstance(attempt_token, UUID) or type(fencing_generation) is not int
                or fencing_generation < 1):
            raise ValueError("DB_WORKER_CONTEXT_INVALID")
        async with self._db.session() as session:
            now = await session.scalar(select(func.clock_timestamp()))
            pair = (await session.execute(
                select(Evaluation, EvaluationJob).join(
                    EvaluationJob, EvaluationJob.evaluation_id == Evaluation.id
                ).where(
                    EvaluationJob.id == job_id,
                    EvaluationJob.organization_id == organization_id,
                    Evaluation.organization_id == organization_id,
                    EvaluationJob.status == "processing",
                    Evaluation.status == "processing",
                    EvaluationJob.worker_id == worker_id,
                    EvaluationJob.attempt_token == attempt_token,
                    EvaluationJob.fencing_generation == fencing_generation,
                    EvaluationJob.lease_until > now,
                )
            )).one_or_none()
            if pair is None:
                return None
            evaluation, job = pair
            return WorkerEvaluationContext(
                evaluation_id=evaluation.id, job_id=job.id,
                organization_id=evaluation.organization_id,
                owner_id=evaluation.owner_id,
                evaluation_type=evaluation.evaluation_type,
                rubric_version_id=evaluation.rubric_version_id,
                protected_text_ref=evaluation.protected_text_ref,
            )

    async def read_scoped_report_async(self, *, organization_id: str,
                                       evaluation_id: UUID):
        """Read only within authenticated tenant; caller must enforce ownership."""
        self._scope(organization_id)
        async with self._db.session() as session:
            evaluation = (await session.scalars(select(Evaluation).where(
                Evaluation.id == evaluation_id,
                Evaluation.organization_id == organization_id,
            ))).one_or_none()
            if evaluation is None:
                return None
            rows = (await session.scalars(select(CriterionResult).where(
                CriterionResult.organization_id == organization_id,
                CriterionResult.evaluation_id == evaluation_id,
            ).order_by(CriterionResult.criterion_code))).all()
            return evaluation, tuple(rows)

