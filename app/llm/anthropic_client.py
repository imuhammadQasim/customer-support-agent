"""Anthropic implementation of :class:`LLMProvider` (skeleton)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

import structlog

from app.core.exceptions import LLMError
from app.llm.base import ChatMessage, LLMResponse, LLMStreamChunk, ToolSpec

try:  # pragma: no cover - import guard so the app runs without the SDK installed
    from anthropic import AsyncAnthropic
except ImportError:  # pragma: no cover
    AsyncAnthropic = None  # type: ignore[assignment, misc]

logger = structlog.get_logger("app.llm.anthropic")


class AnthropicProvider:
    """Provider backed by the Anthropic Messages API."""

    def __init__(self, *, api_key: str, timeout_s: float = 60.0, max_tokens: int = 2048) -> None:
        self._max_tokens = max_tokens
        self._client: Any | None = None
        if AsyncAnthropic is not None and api_key:
            self._client = AsyncAnthropic(api_key=api_key, timeout=timeout_s)

    def _require_client(self) -> Any:
        if self._client is None:
            raise LLMError(
                "Anthropic client is not configured "
                "(missing 'anthropic' package or LLM__ANTHROPIC_API_KEY)."
            )
        return self._client

    @staticmethod
    def _split_messages(
        messages: Sequence[ChatMessage],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Split a flat message list into (system_prompt, turns)."""
        system_parts: list[str] = []
        turns: list[dict[str, Any]] = []
        for message in messages:
            if message.role == "system":
                system_parts.append(message.content)
            elif message.role in ("user", "assistant"):
                turns.append({"role": message.role, "content": message.content})
            else:  # "tool"
                # TODO: convert tool results into Anthropic tool_result content blocks.
                turns.append({"role": "user", "content": message.content})
        return "\n\n".join(system_parts), turns

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
        client = self._require_client()
        system, turns = self._split_messages(messages)
        extra: dict[str, Any] = {}
        if temperature is not None:
            extra["temperature"] = temperature
        # TODO: map ToolSpec -> anthropic `tools=` param and parse tool_use blocks.
        try:
            resp = await client.messages.create(
                model=model,
                system=system or None,
                messages=turns,
                max_tokens=max_tokens or self._max_tokens,
                **extra,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Anthropic completion failed: {exc}") from exc

        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )
        return LLMResponse(
            text=text,
            stop_reason=resp.stop_reason or "stop",
            usage={
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            },
            model=model,
        )

    async def stream(
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
        client = self._require_client()
        system, turns = self._split_messages(messages)
        try:
            async with client.messages.stream(
                model=model,
                system=system or None,
                messages=turns,
                max_tokens=max_tokens or self._max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield LLMStreamChunk(type="text", text=text)
                final = await stream.get_final_message()
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Anthropic stream failed: {exc}") from exc

        # TODO: emit type="tool_call" chunks from final.content tool_use blocks.
        yield LLMStreamChunk(
            type="done",
            stop_reason=final.stop_reason or "stop",
            usage={
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
            },
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.close()
