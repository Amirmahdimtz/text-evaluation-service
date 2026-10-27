"""Stage06 scoped candidate rubric persistence; short audited transactions only."""
from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import AuditEvent, RubricVersion
from src.infrastructure.repositories.base.base_repository import BaseRepository


@inject
class RubricVersionRepository(BaseRepository[RubricVersion]):
    def __init__(self, db_context: PsqlDbContext) -> None:
        super().__init__(db_context, RubricVersion)

    async def get_published_async(
        self, *, organization_id: str, evaluation_type: str,
        code: str | None = None, version: str | None = None,
    ) -> RubricVersion | None:
        self._scope(organization_id)
        if evaluation_type not in ("speech", "media", "research"):
            raise ValueError("DB_EVALUATION_TYPE_INVALID")
        if code is not None and not code:
            raise ValueError("RUBRIC_CODE_INVALID")
        async with self._db.session() as session:
            stmt = select(RubricVersion).where(
                RubricVersion.organization_id == organization_id,
                RubricVersion.evaluation_type == evaluation_type,
                RubricVersion.status == "published",
            )
            if code is not None:
                stmt = stmt.where(RubricVersion.code == code)
            if version is not None:
                stmt = stmt.where(RubricVersion.version == version)
            stmt = stmt.order_by(RubricVersion.published_at.desc(), RubricVersion.id).limit(1)
            return (await session.scalars(stmt)).one_or_none()

    async def insert_candidate_async(
        self, *, organization_id: str, actor_id: str, correlation_id: UUID,
        evaluation_type: str, code: str, version: str, snapshot: dict,
        checksum: str,
    ) -> UUID:
        self._scope(organization_id)
        if not actor_id or not isinstance(correlation_id, UUID):
            raise ValueError("RUBRIC_ACTOR_REQUIRED")
        rid = uuid4()
        try:
            async with self._db.session() as session:
                async with session.begin():
                    session.add(RubricVersion(
                        id=rid, organization_id=organization_id,
                        evaluation_type=evaluation_type, code=code, version=version,
                        criteria_snapshot=snapshot, checksum=checksum, status="draft",
                    ))
                    session.add(AuditEvent(
                        id=uuid4(), organization_id=organization_id, actor_id=actor_id,
                        action_code="RUBRIC_DRAFT_CREATED", resource_kind="rubric",
                        resource_id=rid, correlation_id=correlation_id,
                    ))
                    await session.flush()
        except IntegrityError:
            raise ValueError("RUBRIC_VERSION_CONFLICT") from None
        return rid

    async def get_draft_async(
        self, *, organization_id: str, evaluation_type: str,
        code: str, version: str,
    ) -> RubricVersion | None:
        self._scope(organization_id)
        async with self._db.session() as session:
            return (await session.scalars(select(RubricVersion).where(
                RubricVersion.organization_id == organization_id,
                RubricVersion.evaluation_type == evaluation_type,
                RubricVersion.code == code,
                RubricVersion.version == version,
                RubricVersion.status == "draft",
            ))).one_or_none()

    async def publish_candidate_async(
        self, *, organization_id: str, actor_id: str, correlation_id: UUID,
        rubric_id: UUID, expected_checksum: str, expected_snapshot: dict,
    ) -> UUID:
        self._scope(organization_id)
        if not actor_id or not isinstance(correlation_id, UUID):
            raise ValueError("RUBRIC_ACTOR_REQUIRED")
        async with self._db.session() as session:
            async with session.begin():
                row = (await session.scalars(select(RubricVersion).where(
                    RubricVersion.id == rubric_id,
                    RubricVersion.organization_id == organization_id,
                ).with_for_update())).one_or_none()
                if row is None or row.status != "draft":
                    raise ValueError("RUBRIC_NOT_DRAFT")
                if row.checksum != expected_checksum or row.criteria_snapshot != expected_snapshot:
                    raise ValueError("RUBRIC_SNAPSHOT_CHANGED")
                row.status = "published"
                row.published_at = await session.scalar(select(func.now()))
                session.add(AuditEvent(
                    id=uuid4(), organization_id=organization_id, actor_id=actor_id,
                    action_code="RUBRIC_CANDIDATE_PUBLISHED", resource_kind="rubric",
                    resource_id=row.id, correlation_id=correlation_id,
                ))
        return rubric_id

    async def retire_candidate_async(
        self, *, organization_id: str, actor_id: str,
        correlation_id: UUID, rubric_id: UUID,
    ) -> UUID:
        self._scope(organization_id)
        if not actor_id or not isinstance(correlation_id, UUID):
            raise ValueError("RUBRIC_ACTOR_REQUIRED")
        async with self._db.session() as session:
            async with session.begin():
                row = (await session.scalars(select(RubricVersion).where(
                    RubricVersion.id == rubric_id,
                    RubricVersion.organization_id == organization_id,
                ).with_for_update())).one_or_none()
                if row is None or row.status != "published":
                    raise ValueError("RUBRIC_NOT_PUBLISHED")
                row.status = "retired"  # The Stage05 trigger permits only this state change.
                session.add(AuditEvent(
                    id=uuid4(), organization_id=organization_id, actor_id=actor_id,
                    action_code="RUBRIC_CANDIDATE_RETIRED", resource_kind="rubric",
                    resource_id=row.id, correlation_id=correlation_id,
                ))
        return rubric_id
