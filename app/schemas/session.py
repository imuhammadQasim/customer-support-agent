"""Session + message schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SessionCreate(BaseModel):
    """Payload to open a new session."""

    agent_name: str = Field(default="echo")
    user_id: str | None = None
    title: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class SessionRead(ORMModel):
    """Session as returned by the API."""

    id: str
    agent_name: str
    user_id: str | None
    title: str | None
    status: str
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MessageRead(ORMModel):
    """Message as returned by the API."""

    id: str
    session_id: str
    role: str
    content: str
    token_count: int | None
    created_at: datetime
