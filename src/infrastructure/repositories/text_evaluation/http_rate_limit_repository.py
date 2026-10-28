"""Cross-replica admission, with PostgreSQL clock and atomic UPSERT."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import HttpRateLimit
from src.infrastructure.repositories.base.base_repository import BaseRepository


@inject
class HttpRateLimitRepository(BaseRepository[HttpRateLimit]):
    def __init__(self, db_context: PsqlDbContext) -> None:
        super().__init__(db_context, HttpRateLimit)

    async def consume_async(
        self, *, organization_id: str, user_id: str, max_per_minute: int,
    ) -> bool:
        self._scope(organization_id)
        if (not user_id or type(max_per_minute) is not int
                or not 1 <= max_per_minute <= 10000):
            raise ValueError("RATE_POLICY_INVALID")
        async with self._db.session() as session:
            async with session.begin():
                now = await session.scalar(select(func.date_trunc(
                    "minute", func.clock_timestamp(),
                )))
                query = insert(HttpRateLimit).values(
                    id=uuid4(), organization_id=organization_id,
                    user_id=user_id, window_start=now, hits=1,
                )
                query = query.on_conflict_do_update(
                    constraint="uq_http_rate_limit_window",
                    set_={"hits": HttpRateLimit.hits + 1},
                    where=HttpRateLimit.hits < max_per_minute,
                ).returning(HttpRateLimit.id)
                return (await session.scalar(query)) is not None
