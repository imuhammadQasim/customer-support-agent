"""Provider-agnostic LLM protocol and message types (with tool-calling support)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    """A single message in an LLM conversation."""

    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class ToolSpec(BaseModel):
    """Provider-agnostic description of a callable tool."""

    name: str
    description: str
    input_schema: dict[str, Any]


class LLMToolCall(BaseModel):
    """A tool call requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """A non-streaming completion result."""

    text: str = ""
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    stop_reason: str = "stop"
    usage: dict[str, int] = Field(default_factory=dict)
    model: str = ""


class LLMStreamChunk(BaseModel):
    """One incremental chunk from a streaming completion."""

    type: Literal["text", "tool_call", "done"]
    text: str = ""
    tool_call: LLMToolCall | None = None
    stop_reason: str | None = None
    usage: dict[str, int] | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """The interface every LLM provider implementation must satisfy."""

    async def complete(
        self,
        *,
        messages: Sequence[ChatMessage],
        model: str,
        tools: Sequence[ToolSpec] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Return a full completion."""
        ...

    def stream(
        self,
        *,
        messages: Sequence[ChatMessage],
        model: str,
        tools: Sequence[ToolSpec] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Yield incremental completion chunks."""
        ...

    async def aclose(self) -> None:
        """Release any underlying network resources."""
        ...
