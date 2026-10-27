"""Tenant-scoped single-entity CRUD; one short AsyncSession per operation."""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from src.infrastructure.context.sql_db.psql_dbcontext import Base, PsqlDbContext

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, db_context: PsqlDbContext, model: type[T]) -> None:
        self._db = db_context
        self._model = model

    def _scope(self, organization_id: str, owner_id: str | None = None):
        if not isinstance(organization_id, str) or not organization_id.strip():
            raise ValueError("DB_SCOPE_REQUIRED")
        scope = self._model.organization_id == organization_id
        if hasattr(self._model, "owner_id"):
            if not isinstance(owner_id, str) or not owner_id.strip():
                raise ValueError("DB_OWNER_SCOPE_REQUIRED")
            scope = scope & (self._model.owner_id == owner_id)
        return scope

    async def insert_async(self, entity: T, *, organization_id: str, owner_id: str | None = None) -> T:
        self._scope(organization_id, owner_id)
        if (not isinstance(entity, self._model)
                or entity.organization_id != organization_id
                or (hasattr(entity, "owner_id") and entity.owner_id != owner_id)):
            raise ValueError("DB_SCOPE_MISMATCH")
        async with self._db.session() as session:
            async with session.begin():
                session.add(entity)
            await session.refresh(entity)
        return entity

    async def insert_and_get_id_async(self, entity: T, *, organization_id: str, owner_id: str | None = None) -> UUID:
        return (await self.insert_async(entity, organization_id=organization_id, owner_id=owner_id)).id

    async def get_by_id_async(self, item_id: UUID, *, organization_id: str, owner_id: str | None = None) -> T | None:
        scope = self._scope(organization_id, owner_id)
        async with self._db.session() as session:
            return (await session.scalars(
                select(self._model).where(self._model.id == item_id, scope)
            )).one_or_none()

    async def get_all_async(self, *, organization_id: str, owner_id: str | None = None, limit: int = 100) -> list[T]:
        scope = self._scope(organization_id, owner_id)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("DB_PAGE_LIMIT_INVALID")
        async with self._db.session() as session:
            return list((await session.scalars(
                select(self._model).where(scope).order_by(self._model.id).limit(limit)
            )).all())

    async def update_async(self, entity: T, *, organization_id: str, owner_id: str | None = None) -> T | None:
        scope = self._scope(organization_id, owner_id)
        if (not isinstance(entity, self._model) or entity.organization_id != organization_id
                or (hasattr(entity, "owner_id") and entity.owner_id != owner_id)):
            raise ValueError("DB_SCOPE_MISMATCH")
        async with self._db.session() as session:
            async with session.begin():
                found = (await session.scalars(
                    select(self._model).where(self._model.id == entity.id, scope).with_for_update()
                )).one_or_none()
                if found is None:
                    return None
                merged = await session.merge(entity)
            await session.refresh(merged)
        return merged

    async def delete_async(self, item_id: UUID, *, organization_id: str, owner_id: str | None = None) -> bool:
        scope = self._scope(organization_id, owner_id)
        async with self._db.session() as session:
            async with session.begin():
                found = (await session.scalars(
                    select(self._model).where(self._model.id == item_id, scope).with_for_update()
                )).one_or_none()
                if found is None:
                    return False
                await session.delete(found)
        return True
