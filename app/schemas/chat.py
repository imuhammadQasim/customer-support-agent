"""Chat request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """One user turn submitted to the chat endpoint."""

    message: str = Field(..., min_length=1)


class ChatReply(BaseModel):
    """The assistant's answer for one turn."""

    session_id: str
    reply: str
