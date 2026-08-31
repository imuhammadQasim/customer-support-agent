"""Agent runtime: assemble context (memory + tools + llm) and drive the event stream."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable

import structlog

from app.agents.base import AgentContext
from app.agents.memory.base import MemoryTurn, SessionMemory
from app.agents.registry import get_agent
from app.agents.tools.registry import ToolRegistry
from app.core.config import Settings
from app.core.exceptions import AppError
from app.llm.router import LLMRouter
from app.schemas.agent_events import AgentEvent, DoneEvent, ErrorEvent, TokenEvent

logger = structlog.get_logger("app.agents.runtime")


class AgentRuntime:
    """Stateless orchestrator that runs a named agent for one turn."""

    def __init__(
        self,
        *,
        llm_router: LLMRouter,
        tool_registry: ToolRegistry,
        memory_factory: Callable[[str], SessionMemory],
        settings: Settings,
    ) -> None:
        self._llm_router = llm_router
        self._tools = tool_registry
        self._memory_factory = memory_factory
        self._settings = settings

    async def stream(
        self, *, agent_name: str, session_id: str, user_input: str
    ) -> AsyncIterator[AgentEvent]:
        """Run ``agent_name`` for ``user_input`` and yield its events."""
        import app.agents  # noqa: F401  ensure agent/tool registration side effects

        agent_cls = get_agent(agent_name)
        memory = self._memory_factory(session_id)
        history = await memory.get_history()
        context = AgentContext(
            session_id=session_id,
            history=history,
            llm_router=self._llm_router,
            tools=self._tools,
            memory=memory,
            settings=self._settings,
        )
        agent = agent_cls(context)

        await memory.append(MemoryTurn(role="user", content=user_input))

        parts: list[str] = []
        try:
            async for event in agent.stream(user_input):
                if isinstance(event, TokenEvent):
                    parts.append(event.text)
                yield event
        except AppError as exc:
            logger.warning("agent.stream.app_error", code=exc.code, agent=agent_name)
            yield ErrorEvent(code=exc.code, message=exc.message)
            yield DoneEvent(reason="error")
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent.stream.crashed", agent=agent_name)
            yield ErrorEvent(code="internal_error", message=str(exc))
            yield DoneEvent(reason="error")
            return

        await memory.append(MemoryTurn(role="assistant", content="".join(parts)))
