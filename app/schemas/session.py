"""Session + message schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.services.session_store import Message, Session


class SessionCreate(BaseModel):
    """Payload to open a new session."""

    title: str | None = None


class MessageRead(BaseModel):
    """A message as returned by the API."""

    role: str
    content: str
    created_at: datetime

    @classmethod
    def of(cls, message: Message) -> MessageRead:
        return cls(role=message.role, content=message.content, created_at=message.created_at)


class SessionRead(BaseModel):
    """A session as returned by the API."""

    id: str
    title: str | None
    created_at: datetime
    message_count: int = Field(description="Number of stored turns.")

    @classmethod
    def of(cls, session: Session) -> SessionRead:
        return cls(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            message_count=len(session.messages),
        )
