"""Reference agent: echoes user input token-by-token.

Domain-agnostic. `/tool <text>` exercises the sample tool to demonstrate the loop.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.agents.base import BaseAgent
from app.agents.prompts.echo import SYSTEM_PROMPT
from app.agents.registry import register_agent
from app.schemas.agent_events import (
    AgentEvent,
    DoneEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from app.utils.ids import new_uuid


def _tokenize(text: str) -> list[str]:
    """Split text into whitespace-preserving pseudo-tokens."""
    parts = text.split(" ")
    return [p + (" " if i < len(parts) - 1 else "") for i, p in enumerate(parts)]


@register_agent
class EchoAgent(BaseAgent):
    """Echoes input; a minimal implementation of the agent contract."""

    name = "echo"
    description = "Echo agent (reference implementation)."

    async def stream(self, user_input: str) -> AsyncIterator[AgentEvent]:
        """Stream the echoed response (optionally via the sample tool)."""
        seq = 0
        _ = SYSTEM_PROMPT
        # TODO: build messages from SYSTEM_PROMPT + self.context.history and call
        #       self.context.llm_router.stream(TaskType.CHAT, messages, tools=...).
        text = user_input

        if user_input.startswith("/tool "):
            argument = user_input.removeprefix("/tool ").strip()
            call_id = new_uuid()
            yield ToolCallEvent(
                seq=seq, call_id=call_id, name="sample_tool", arguments={"text": argument}
            )
            seq += 1
            tool = self.context.tools.get("sample_tool")
            result = await tool({"text": argument})
            yield ToolResultEvent(
                seq=seq,
                call_id=call_id,
                name="sample_tool",
                result=result.content,
                ok=result.ok,
            )
            seq += 1
            text = str(result.content)

        for token in _tokenize(text):
            yield TokenEvent(seq=seq, text=token)
            seq += 1

        yield DoneEvent(seq=seq, reason="stop")
