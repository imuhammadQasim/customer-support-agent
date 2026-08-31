"""Agent package. Importing it registers the built-in agents and tools."""

from app.agents import tools as _tools  # noqa: F401  (triggers tool registration)
from app.agents import echo_agent as _echo_agent  # noqa: F401  (triggers agent registration)
