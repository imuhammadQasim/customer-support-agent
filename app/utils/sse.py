"""Server-Sent Events formatting helpers."""

from __future__ import annotations

from app.schemas.agent_events import AgentEvent, agent_event_adapter

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def format_sse(event: AgentEvent, *, event_name: str | None = None) -> str:
    """Serialize an :class:`AgentEvent` into a single SSE frame."""
    name = event_name or getattr(event, "type", "message")
    data = agent_event_adapter.dump_json(event).decode()
    return f"event: {name}\ndata: {data}\n\n"
