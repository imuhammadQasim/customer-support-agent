"""SSE streaming chat endpoint. Delegates all logic to ChatService."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import ChatServiceDep
from app.schemas.chat import ChatRequest
from app.utils.sse import SSE_HEADERS, format_sse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{session_id}/stream")
async def chat_stream(
    session_id: str,
    payload: ChatRequest,
    service: ChatServiceDep,
) -> StreamingResponse:
    """Stream :class:`AgentEvent` objects for one turn as Server-Sent Events."""
    # Validate the session up front so a 404 returns a normal JSON envelope
    # (an error raised mid-stream cannot change the response status).
    await service.ensure_session(session_id)

    async def event_source() -> AsyncIterator[str]:
        async for event in service.stream_reply(
            session_id=session_id,
            message=payload.message,
            agent_name=payload.agent_name,
            tier=payload.tier,
        ):
            yield format_sse(event)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
