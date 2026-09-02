"""Chat endpoint. Delegates the LLM work to ChatService."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ChatServiceDep
from app.schemas.chat import ChatReply, ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{session_id}", response_model=ChatReply)
async def chat(session_id: str, payload: ChatRequest, service: ChatServiceDep) -> ChatReply:
    """Send one message and get the assistant's reply (full response, not streamed)."""
    reply = await service.reply(session_id=session_id, message=payload.message)
    return ChatReply(session_id=session_id, reply=reply)
