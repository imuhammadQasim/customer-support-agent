"""Session lifecycle use cases."""

from __future__ import annotations

from collections.abc import Sequence

from app.core.exceptions import NotFoundError
from app.models.message import Message
from app.models.session import Session
from app.repositories.message import MessageRepository
from app.repositories.session import SessionRepository
from app.schemas.session import SessionCreate


class SessionService:
    """Create, read, and delete sessions and their messages."""

    def __init__(self, *, session_repo: SessionRepository, message_repo: MessageRepository) -> None:
        self._sessions = session_repo
        self._messages = message_repo

    async def create_session(self, payload: SessionCreate) -> Session:
        """Open a new session."""
        # TODO: validate payload.agent_name against app.agents.registry.available_agents().
        return await self._sessions.create(payload.model_dump())

    async def get_session(self, session_id: str) -> Session:
        """Fetch a session or raise :class:`NotFoundError`."""
        session = await self._sessions.get(session_id)
        if session is None:
            raise NotFoundError(f"Session not found: {session_id}")
        return session

    async def list_messages(
        self, session_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Message]:
        """List a session's messages."""
        await self.get_session(session_id)
        return await self._messages.list_for_session(session_id, limit=limit, offset=offset)

    async def delete_session(self, session_id: str) -> None:
        """Delete a session (and cascade its messages)."""
        session = await self.get_session(session_id)
        await self._sessions.delete(session.id)
