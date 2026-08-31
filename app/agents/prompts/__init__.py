"""Prompt templates for built-in agents."""

from app.agents.prompts.echo import SYSTEM_PROMPT as ECHO_SYSTEM_PROMPT
from app.agents.prompts.echo import render_system_prompt

__all__ = ["ECHO_SYSTEM_PROMPT", "render_system_prompt"]
