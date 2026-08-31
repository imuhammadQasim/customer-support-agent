"""Contract for outbound integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseIntegration(ABC):
    """Base class for a client that talks to an external system."""

    name: str = ""

    @abstractmethod
    async def healthcheck(self) -> bool:
        """Return True if the remote system is reachable and healthy."""
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release pooled clients / sessions."""
        # TODO: override in subclasses that hold long-lived connections.
        return None
