"""Message repository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """CRUD for :class:`Message`."""

    model = Message

    async def list_for_session(
        self, session_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Message]:
        """Return a session's messages, oldest first."""
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
