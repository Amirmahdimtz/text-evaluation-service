"""Lazy per-process PostgreSQL async engine; local Stage 05 isolation is mandatory."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.di.inject import inject


class Base(DeclarativeBase):
    pass


def get_test_database_url() -> str:
    """Fail closed: migrations and tests may access only an explicitly isolated local DB."""
    if os.environ.get("TES_ENVIRONMENT", "development") != "development":
        raise ValueError("STAGE05_LOCAL_DATABASE_ONLY")
    raw = os.environ.get("TES_STAGE05_DATABASE_URL", "")
    try:
        url = make_url(raw)
        if (url.drivername != "postgresql+asyncpg"
                or url.host not in ("localhost", "127.0.0.1")
                or not url.database or not url.database.startswith("tes_stage05_")
                or not url.username or url.query):
            raise ValueError
    except (ValueError, AttributeError):
        raise ValueError("STAGE05_ISOLATED_DATABASE_URL_REQUIRED") from None
    return raw


@inject
class PsqlDbContext:
    """Singleton engine/factory; a new AsyncSession is created per operation."""

    __di_singleton__ = True

    def __init__(self) -> None:
        self._engine = None
        self._factory: async_sessionmaker[AsyncSession] | None = None

    def session(self) -> AsyncSession:
        if self._factory is None:
            # Deliberately lazy: starting the Stage04 app never connects to a DB.
            url = get_test_database_url()
            self._engine = create_async_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=0)
            self._factory = async_sessionmaker(self._engine, expire_on_commit=False)
        return self._factory()

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._factory = None
