"""Abstract agent contract + run-time context object."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, Field

from app.schemas.agent_events import AgentEvent, TokenEvent

if TYPE_CHECKING:
    from app.agents.memory.base import MemoryTurn, SessionMemory
    from app.agents.tools.registry import ToolRegistry
    from app.core.config import Settings
    from app.llm.router import LLMRouter


@dataclass(slots=True)
class AgentContext:
    """Everything an agent needs at run time, assembled by the AgentRuntime."""

    session_id: str
    history: list["MemoryTurn"]
    llm_router: "LLMRouter"
    tools: "ToolRegistry"
    memory: "SessionMemory"
    settings: "Settings"
    extra: dict[str, object] = field(default_factory=dict)


class AgentRunResult(BaseModel):
    """Aggregate outcome of a non-streaming ``run``."""

    output: str
    events: list[AgentEvent] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract agent. Subclasses implement :meth:`stream`; :meth:`run` is derived."""

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    @abstractmethod
    def stream(self, user_input: str) -> AsyncIterator[AgentEvent]:
        """Yield :class:`AgentEvent` objects as the turn progresses."""
        raise NotImplementedError

    async def run(self, user_input: str) -> AgentRunResult:
        """Consume :meth:`stream` to completion and return the aggregate result."""
        events: list[AgentEvent] = []
        parts: list[str] = []
        async for event in self.stream(user_input):
            events.append(event)
            if isinstance(event, TokenEvent):
                parts.append(event.text)
        return AgentRunResult(output="".join(parts), events=events)
