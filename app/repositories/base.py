"""Generic async CRUD repository."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD operations for one model type. Subclasses set ``model``."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: Any) -> ModelT | None:
        """Return a row by primary key, or ``None``."""
        return await self.session.get(self.model, id_)

    async def get_or_404(self, id_: Any) -> ModelT:
        """Return a row by primary key or raise :class:`NotFoundError`."""
        obj = await self.get(id_)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} not found: {id_}")
        return obj

    async def list(self, *, limit: int = 50, offset: int = 0, **filters: Any) -> Sequence[ModelT]:
        """Return rows matching simple equality ``filters``."""
        stmt = select(self.model).limit(limit).offset(offset)
        for attr, value in filters.items():
            stmt = stmt.where(getattr(self.model, attr) == value)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, values: Mapping[str, Any]) -> ModelT:
        """Insert a new row and return it."""
        obj = self.model(**values)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id_: Any, values: Mapping[str, Any]) -> ModelT:
        """Patch an existing row and return it."""
        obj = await self.get_or_404(id_)
        for attr, value in values.items():
            setattr(obj, attr, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id_: Any) -> None:
        """Delete a row by primary key."""
        obj = await self.get_or_404(id_)
        await self.session.delete(obj)
        await self.session.flush()
