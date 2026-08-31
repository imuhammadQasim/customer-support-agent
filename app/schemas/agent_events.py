"""Discriminated union of streaming agent events."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class _BaseEvent(BaseModel):
    """Fields common to every agent event."""

    seq: int = Field(default=0, description="Monotonic sequence number within a run.")


class TokenEvent(_BaseEvent):
    """A chunk of generated text."""

    type: Literal["token"] = "token"
    text: str


class ToolCallEvent(_BaseEvent):
    """The agent decided to call a tool."""

    type: Literal["tool_call"] = "tool_call"
    call_id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResultEvent(_BaseEvent):
    """A tool returned a result."""

    type: Literal["tool_result"] = "tool_result"
    call_id: str
    name: str
    result: Any = None
    ok: bool = True


class ErrorEvent(_BaseEvent):
    """A recoverable error occurred during the run."""

    type: Literal["error"] = "error"
    code: str
    message: str


class DoneEvent(_BaseEvent):
    """Terminal event for a run."""

    type: Literal["done"] = "done"
    reason: Literal["stop", "length", "error", "cancelled"] = "stop"
    usage: dict[str, int] | None = None


AgentEvent = Annotated[
    Union[TokenEvent, ToolCallEvent, ToolResultEvent, ErrorEvent, DoneEvent],
    Field(discriminator="type"),
]

agent_event_adapter: TypeAdapter[AgentEvent] = TypeAdapter(AgentEvent)
