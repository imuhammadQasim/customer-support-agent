"""Typed application configuration via pydantic-settings.

Environment variables use a nested delimiter, e.g. ``LLM__ANTHROPIC_API_KEY``.
Copy ``.env.example`` to ``.env`` and fill in your Anthropic key.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    """General application settings."""

    name: str = "customer-support-agent"
    env: str = "local"
    debug: bool = True
    version: str = "0.1.0"
    api_prefix: str = "/api"


class LLMConfig(BaseModel):
    """LangChain / Anthropic model settings."""

    anthropic_api_key: str = ""
    model: str = "claude-sonnet-5"
    max_tokens: int = 1024
    temperature: float = 0.0
    timeout_s: float = 60.0


class Settings(BaseSettings):
    """Root settings object composed of nested config groups."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
