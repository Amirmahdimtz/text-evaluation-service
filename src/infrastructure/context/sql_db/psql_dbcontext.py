"""Async PostgreSQL connection factory; never shares an AsyncSession."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.infrastructure.di.inject import inject

class Base(DeclarativeBase):
    pass

@inject
class PsqlDbContext:
    __di_singleton__ = True

    def __init__(self) -> None:
        url = os.environ.get("TES_DATABASE_URL", "")
        if not url.startswith("postgresql+asyncpg://") or "@" not in url:
            raise ValueError("DATABASE_URL_INVALID")
        self._engine = create_async_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)
        self._factory = async_sessionmaker(self._engine, expire_on_commit=False, autoflush=False)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._factory() as session:
            yield session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        async with self._factory.begin() as session:
            yield session

    async def dispose_async(self) -> None:
        await self._engine.dispose()
