"""Decorator-based agent registry."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.exceptions import NotFoundError

_AGENTS: dict[str, type[BaseAgent]] = {}


def register_agent(cls: type[BaseAgent]) -> type[BaseAgent]:
    """Class decorator: register an agent class under its ``name``."""
    if not getattr(cls, "name", ""):
        raise ValueError(f"{cls.__name__} must set a non-empty class attribute `name`.")
    _AGENTS[cls.name] = cls
    return cls


def get_agent(name: str) -> type[BaseAgent]:
    """Return a registered agent class or raise :class:`NotFoundError`."""
    try:
        return _AGENTS[name]
    except KeyError:
        raise NotFoundError(f"Unknown agent: {name!r}") from None


def available_agents() -> list[str]:
    """Return the sorted names of all registered agents."""
    return sorted(_AGENTS)
