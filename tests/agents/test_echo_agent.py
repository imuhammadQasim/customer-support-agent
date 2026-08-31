"""EchoAgent unit tests (no HTTP, no DB)."""

from __future__ import annotations

from app.agents.base import AgentContext
from app.agents.echo_agent import EchoAgent
from app.agents.memory.base import MemoryTurn
from app.agents.tools.registry import ToolRegistry
from app.schemas.agent_events import DoneEvent, TokenEvent


class _NullMemory:
    """In-memory no-op SessionMemory for isolated agent tests."""

    async def append(self, turn: MemoryTurn) -> None:
        return None

    async def get_history(self, *, limit: int | None = None) -> list[MemoryTurn]:
        return []

    async def clear(self) -> None:
        return None


async def test_echo_agent_streams_tokens_then_done() -> None:
    """stream() yields TokenEvents for the input and ends with a DoneEvent."""
    context = AgentContext(
        session_id="s1",
        history=[],
        llm_router=None,  # type: ignore[arg-type]
        tools=ToolRegistry.default(),
        memory=_NullMemory(),  # type: ignore[arg-type]
        settings=None,  # type: ignore[arg-type]
    )
    agent = EchoAgent(context)

    events = [event async for event in agent.stream("alpha beta")]

    assert any(isinstance(e, TokenEvent) for e in events)
    assert isinstance(events[-1], DoneEvent)
    text = "".join(e.text for e in events if isinstance(e, TokenEvent))
    assert "alpha" in text and "beta" in text
