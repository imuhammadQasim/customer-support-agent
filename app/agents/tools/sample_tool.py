"""Sample tool: a domain-agnostic string transform to demonstrate the pattern."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.tools.registry import register_tool


class SampleToolArgs(BaseModel):
    """Arguments for :class:`SampleTool`."""

    text: str = Field(..., description="Arbitrary input string to transform.")
    uppercase: bool = Field(default=False, description="Also upper-case the output.")


@register_tool
class SampleTool(BaseTool[SampleToolArgs]):
    """Reverse a string. Placeholder for a real side-effecting capability."""

    name = "sample_tool"
    description = "Reverse a string (demo tool)."
    args_schema = SampleToolArgs

    async def execute(self, args: SampleToolArgs) -> ToolResult:
        """Return the reversed input."""
        # TODO: replace with real logic (HTTP call, DB read, computation, ...).
        out = args.text[::-1]
        if args.uppercase:
            out = out.upper()
        return ToolResult(ok=True, content=out)
