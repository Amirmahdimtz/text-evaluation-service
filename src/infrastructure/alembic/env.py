"""Alembic migration environment: localhost test database only, no autogeneration."""
from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from src.infrastructure.context.sql_db.psql_dbcontext import Base, get_test_database_url
from src.infrastructure.models import text_evaluation  # noqa: F401 - metadata registration

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    raise RuntimeError("STAGE05_OFFLINE_MIGRATION_DISABLED")


def run_migrations_online() -> None:
    async def migrate() -> None:
        engine = create_async_engine(get_test_database_url(), pool_pre_ping=True)
        try:
            async with engine.connect() as conn:
                await conn.run_sync(
                    lambda connection: _configure_and_run(connection)
                )
        finally:
            await engine.dispose()

    asyncio.run(migrate())


def _configure_and_run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        transactional_ddl=True,
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
