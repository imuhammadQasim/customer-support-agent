"""Session repository."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.session import Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """CRUD for :class:`Session`."""

    model = Session

    async def list_for_user(
        self, user_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Session]:
        """Return sessions owned by ``user_id``."""
        return await self.list(limit=limit, offset=offset, user_id=user_id)
