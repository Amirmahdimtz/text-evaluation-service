"""Scope-authorized append-only encrypted feedback and minimal audit event."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import AuditEvent, Evaluation, EvaluationFeedback
from src.infrastructure.repositories.base.base_repository import BaseRepository


@inject
class EvaluationFeedbackRepository(BaseRepository[EvaluationFeedback]):
    def __init__(self, db_context: PsqlDbContext) -> None:
        super().__init__(db_context, EvaluationFeedback)

    async def append_authorized_async(
        self, *, organization_id: str, reviewer_id: str,
        assigned_evaluation_ids: frozenset[UUID],
        evaluation_id: UUID, revision: int, decision_code: str,
        encrypted_details: bytes, correlation_id: UUID,
    ) -> UUID:
        self._scope(organization_id)
        if (not reviewer_id or evaluation_id not in assigned_evaluation_ids
                or type(revision) is not int or revision < 1
                or not isinstance(decision_code, str) or not 0 < len(decision_code) <= 64
                or not isinstance(encrypted_details, bytes) or not encrypted_details):
            raise ValueError("DB_FEEDBACK_NOT_AUTHORIZED")
        feedback = EvaluationFeedback(
            id=uuid4(), evaluation_id=evaluation_id, organization_id=organization_id,
            reviewer_id=reviewer_id, revision=revision, decision_code=decision_code,
            encrypted_details=encrypted_details,
        )
        async with self._db.session() as session:
            async with session.begin():
                exists = (await session.scalars(select(Evaluation.id).where(
                    Evaluation.id == evaluation_id,
                    Evaluation.organization_id == organization_id,
                ))).one_or_none()
                if exists is None:
                    raise ValueError("DB_FEEDBACK_NOT_AUTHORIZED")
                session.add(feedback)
                session.add(AuditEvent(
                    organization_id=organization_id, actor_id=reviewer_id,
                    action_code="FEEDBACK_ADDED", resource_kind="evaluation",
                    resource_id=evaluation_id, correlation_id=correlation_id,
                ))
        return feedback.id
