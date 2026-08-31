"""SessionMemory interface + the turn record it stores."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.utils.time import utcnow

MemoryRole = Literal["system", "user", "assistant", "tool"]


class MemoryTurn(BaseModel):
    """One stored conversation turn."""

    role: MemoryRole
    content: str
    ts: datetime = Field(default_factory=utcnow)


class SessionMemory(ABC):
    """Short-term conversation memory for a single session."""

    @abstractmethod
    async def append(self, turn: MemoryTurn) -> None:
        """Append a turn to the history."""
        raise NotImplementedError

    @abstractmethod
    async def get_history(self, *, limit: int | None = None) -> list[MemoryTurn]:
        """Return stored turns, oldest first (optionally only the last ``limit``)."""
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """Drop all stored turns for this session."""
        raise NotImplementedError
