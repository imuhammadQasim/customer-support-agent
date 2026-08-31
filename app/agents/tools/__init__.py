"""Tool package. Importing it registers the built-in tools."""

from app.agents.tools import sample_tool as _sample_tool  # noqa: F401  (triggers registration)
