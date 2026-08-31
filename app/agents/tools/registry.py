"""Decorator-based tool registry + a per-runtime tool collection."""

from __future__ import annotations

from collections.abc import Iterable

from app.agents.tools.base import BaseTool
from app.core.exceptions import ToolExecutionError
from app.llm.base import ToolSpec

_TOOL_CLASSES: dict[str, type[BaseTool]] = {}


def register_tool(cls: type[BaseTool]) -> type[BaseTool]:
    """Class decorator: register a tool class under its ``name``."""
    if not getattr(cls, "name", ""):
        raise ValueError(f"{cls.__name__} must set a non-empty class attribute `name`.")
    _TOOL_CLASSES[cls.name] = cls
    return cls


def tool_classes() -> dict[str, type[BaseTool]]:
    """Return a copy of the global {name: tool class} mapping."""
    return dict(_TOOL_CLASSES)


class ToolRegistry:
    """An instantiated set of tools handed to an agent via :class:`AgentContext`."""

    def __init__(self, tools: Iterable[BaseTool]) -> None:
        self._tools: dict[str, BaseTool] = {tool.name: tool for tool in tools}

    @classmethod
    def default(cls) -> "ToolRegistry":
        """Build a registry containing one instance of every registered tool."""
        from app.agents import tools as _tools  # noqa: F401  trigger registration

        return cls(tool_cls() for tool_cls in _TOOL_CLASSES.values())

    def get(self, name: str) -> BaseTool:
        """Return a tool instance by name."""
        try:
            return self._tools[name]
        except KeyError:
            raise ToolExecutionError(f"Unknown tool: {name!r}") from None

    def list(self) -> list[BaseTool]:
        """Return all tool instances."""
        return list(self._tools.values())

    def to_llm_specs(self) -> list[ToolSpec]:
        """Return provider-agnostic specs for LLM tool-calling."""
        return [
            ToolSpec(
                name=tool.name,
                description=tool.description,
                input_schema=tool.args_schema.model_json_schema(),
            )
            for tool in self._tools.values()
        ]
