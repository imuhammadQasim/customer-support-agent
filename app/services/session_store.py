"""In-memory conversation store.

This is the one place that "persists" data. It lives in a plain dict, so
everything is lost when the server restarts. That is fine for learning; when
you want real persistence, swap this module for a database-backed repository
and keep the same method names.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.core.exceptions import NotFoundError
from app.utils.ids import new_uuid
from app.utils.time import utcnow


@dataclass
class Message:
    """A single turn in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Session:
    """A conversation: an id plus its ordered messages."""

    id: str = field(default_factory=new_uuid)
    title: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    messages: list[Message] = field(default_factory=list)


class SessionStore:
    """CRUD over conversations, held in memory."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, *, title: str | None = None) -> Session:
        session = Session(title=title)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise NotFoundError(f"Session not found: {session_id}")
        return session

    def list(self) -> list[Session]:
        return list(self._sessions.values())

    def delete(self, session_id: str) -> None:
        if self._sessions.pop(session_id, None) is None:
            raise NotFoundError(f"Session not found: {session_id}")

    def add_message(self, session_id: str, *, role: str, content: str) -> Message:
        session = self.get(session_id)
        message = Message(role=role, content=content)
        session.messages.append(message)
        return message


# Process-wide singleton. Import this where you need the store.
store = SessionStore()
