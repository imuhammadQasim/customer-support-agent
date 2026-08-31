"""Chat request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """One user turn submitted to the streaming chat endpoint."""

    message: str = Field(..., min_length=1)
    agent_name: str | None = Field(
        default=None, description="Overrides the session's default agent for this turn."
    )
    tier: str | None = Field(
        default=None, description="Optional model tier override: fast | balanced | deep."
    )


class ChatResponse(BaseModel):
    """Non-streaming aggregate response (for a future POST /chat endpoint)."""

    session_id: str
    output: str
    usage: dict[str, int] = Field(default_factory=dict)
