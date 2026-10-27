"""Stage05 tenant-safe lazy async PostgreSQL context; never share AsyncSession."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.di.inject import inject


class Base(DeclarativeBase):
    pass


def get_test_database_url() -> str:
    """Only explicitly isolated loopback development databases may be migrated."""
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
    except (ValueError, AttributeError, ArgumentError):
        raise ValueError("STAGE05_ISOLATED_DATABASE_URL_REQUIRED") from None
    return raw


@inject
class PsqlDbContext:
    """Singleton engine and factory, one async session per repository operation."""

    __di_singleton__ = True

    def __init__(self) -> None:
        self._engine = None
        self._factory: async_sessionmaker[AsyncSession] | None = None

    def _ensure_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._factory is None:
            url = get_test_database_url()
            self._engine = create_async_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=0)
            self._factory = async_sessionmaker(self._engine, expire_on_commit=False, autoflush=False)
        return self._factory

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._ensure_factory()() as session:
            yield session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        """Optional short compound-operation transaction; no LLM calls inside."""
        async with self._ensure_factory().begin() as session:
            yield session

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._factory = None

    async def dispose_async(self) -> None:
        await self.close()
