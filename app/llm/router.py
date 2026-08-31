"""Model-tier router: pick a model per task type (fast / balanced / deep)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from enum import StrEnum

from app.core.config import Settings
from app.llm.base import ChatMessage, LLMProvider, LLMResponse, LLMStreamChunk, ToolSpec


class ModelTier(StrEnum):
    """Coarse capability/cost tiers."""

    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"


class TaskType(StrEnum):
    """What the caller is trying to do; drives default tier selection."""

    CHAT = "chat"
    SUMMARIZE = "summarize"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    PLAN = "plan"
    TOOL_USE = "tool_use"


# Default routing table. TODO: tune per task and/or load overrides from config.
_TASK_TIER: dict[TaskType, ModelTier] = {
    TaskType.CHAT: ModelTier.BALANCED,
    TaskType.SUMMARIZE: ModelTier.FAST,
    TaskType.CLASSIFY: ModelTier.FAST,
    TaskType.EXTRACT: ModelTier.FAST,
    TaskType.PLAN: ModelTier.DEEP,
    TaskType.TOOL_USE: ModelTier.BALANCED,
}


class LLMRouter:
    """Selects a concrete model id for a task and forwards to the provider."""

    def __init__(self, provider: LLMProvider, settings: Settings) -> None:
        self._provider = provider
        self._settings = settings
        self._tier_model: dict[ModelTier, str] = {
            ModelTier.FAST: settings.llm.fast_model,
            ModelTier.BALANCED: settings.llm.balanced_model,
            ModelTier.DEEP: settings.llm.deep_model,
        }

    def select_model(self, task_type: TaskType, *, tier_override: ModelTier | None = None) -> str:
        """Resolve a model id for ``task_type``."""
        tier = tier_override or _TASK_TIER.get(task_type, ModelTier.BALANCED)
        return self._tier_model[tier]

    async def complete(
        self,
        task_type: TaskType,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
        tier_override: ModelTier | None = None,
        **kwargs: object,
    ) -> LLMResponse:
        """Route + call :meth:`LLMProvider.complete`."""
        model = self.select_model(task_type, tier_override=tier_override)
        return await self._provider.complete(
            messages=messages, model=model, tools=tools, **kwargs
        )

    def stream(
        self,
        task_type: TaskType,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
        tier_override: ModelTier | None = None,
        **kwargs: object,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Route + call :meth:`LLMProvider.stream`."""
        model = self.select_model(task_type, tier_override=tier_override)
        return self._provider.stream(messages=messages, model=model, tools=tools, **kwargs)
