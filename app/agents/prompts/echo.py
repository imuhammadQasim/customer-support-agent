"""Prompt text for the echo agent."""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a minimal echo agent used as a reference implementation.\n"
    "Repeat the user's message back to them verbatim. Do not add commentary."
)


def render_system_prompt(**context: str) -> str:
    """Render the system prompt with optional ``{placeholder}`` substitutions.

    TODO: swap for a real template engine (e.g. jinja2) if prompts grow.
    """
    return SYSTEM_PROMPT.format(**context) if context else SYSTEM_PROMPT
