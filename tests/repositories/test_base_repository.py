"""Generic BaseRepository CRUD tests via SessionRepository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.session import SessionRepository


async def test_base_repository_crud(db_session: AsyncSession) -> None:
    """create -> get -> update -> delete round-trips through the DB."""
    repo = SessionRepository(db_session)

    created = await repo.create({"agent_name": "echo"})
    assert created.id
    assert created.status == "active"

    fetched = await repo.get(created.id)
    assert fetched is not None

    updated = await repo.update(created.id, {"status": "closed"})
    assert updated.status == "closed"

    await repo.delete(created.id)
    assert await repo.get(created.id) is None
