"""Chat use case: persist turns and stream agent events."""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.agents.runtime import AgentRuntime
from app.core.exceptions import NotFoundError
from app.llm.router import ModelTier
from app.models.session import Session
from app.repositories.message import MessageRepository
from app.repositories.session import SessionRepository
from app.schemas.agent_events import AgentEvent, TokenEvent


class ChatService:
    """Durable persistence around :class:`AgentRuntime` streaming."""

    def __init__(
        self,
        *,
        session_repo: SessionRepository,
        message_repo: MessageRepository,
        runtime: AgentRuntime,
    ) -> None:
        self._sessions = session_repo
        self._messages = message_repo
        self._runtime = runtime

    async def ensure_session(self, session_id: str) -> Session:
        """Return the session or raise :class:`NotFoundError`."""
        session = await self._sessions.get(session_id)
        if session is None:
            raise NotFoundError(f"Session not found: {session_id}")
        return session

    async def stream_reply(
        self,
        *,
        session_id: str,
        message: str,
        agent_name: str | None = None,
        tier: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """Persist the user turn, stream agent events, then persist the assistant turn."""
        session = await self.ensure_session(session_id)
        agent = agent_name or session.agent_name
        _tier_override = ModelTier(tier) if tier else None
        # TODO: thread _tier_override through AgentRuntime -> AgentContext -> LLMRouter.

        await self._messages.create(
            {"session_id": session_id, "role": "user", "content": message}
        )

        assistant_parts: list[str] = []
        async for event in self._runtime.stream(
            agent_name=agent, session_id=session_id, user_input=message
        ):
            if isinstance(event, TokenEvent):
                assistant_parts.append(event.text)
            yield event

        await self._messages.create(
            {
                "session_id": session_id,
                "role": "assistant",
                "content": "".join(assistant_parts),
            }
        )
        # TODO: persist token usage; bump session.updated_at / status.
