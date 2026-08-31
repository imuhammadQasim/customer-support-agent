"""Abstract tool contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel

from app.core.exceptions import ToolExecutionError

ArgsT = TypeVar("ArgsT", bound=BaseModel)


class ToolResult(BaseModel):
    """Normalised return value of any tool."""

    ok: bool = True
    content: Any = None
    error: str | None = None


class BaseTool(ABC, Generic[ArgsT]):
    """A callable capability an agent can invoke.

    Subclasses set ``name``, ``description``, and ``args_schema`` and implement
    :meth:`execute`. Calling the instance validates raw args before dispatch.
    """

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    args_schema: ClassVar[type[BaseModel]]

    async def __call__(self, raw_args: dict[str, Any]) -> ToolResult:
        """Validate ``raw_args`` then run :meth:`execute`, normalising errors."""
        try:
            args = self.args_schema.model_validate(raw_args)
        except Exception as exc:  # noqa: BLE001
            raise ToolExecutionError(
                f"Invalid arguments for tool {self.name!r}: {exc}"
            ) from exc
        try:
            return await self.execute(args)  # type: ignore[arg-type]
        except ToolExecutionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ToolExecutionError(f"Tool {self.name!r} failed: {exc}") from exc

    @abstractmethod
    async def execute(self, args: ArgsT) -> ToolResult:
        """Run the tool with validated ``args``."""
        raise NotImplementedError
