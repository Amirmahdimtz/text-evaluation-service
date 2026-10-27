"""Read-only published rubric lookup; publication workflow belongs to Stage 06."""
from __future__ import annotations

from sqlalchemy import select
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import RubricVersion
from src.infrastructure.repositories.base.base_repository import BaseRepository


@inject
class RubricVersionRepository(BaseRepository[RubricVersion]):
    def __init__(self, db_context: PsqlDbContext) -> None:
        super().__init__(db_context, RubricVersion)

    async def get_published_async(
        self, *, organization_id: str, evaluation_type: str, code: str | None = None
    ) -> RubricVersion | None:
        self._scope(organization_id)
        if evaluation_type not in ("speech", "media", "research"):
            raise ValueError("DB_EVALUATION_TYPE_INVALID")
        async with self._db.session() as session:
            stmt = select(RubricVersion).where(
                RubricVersion.organization_id == organization_id,
                RubricVersion.evaluation_type == evaluation_type,
                RubricVersion.status == "published",
            )
            if code is not None:
                stmt = stmt.where(RubricVersion.code == code)
            stmt = stmt.order_by(RubricVersion.published_at.desc(), RubricVersion.id).limit(1)
            return (await session.scalars(stmt)).one_or_none()
