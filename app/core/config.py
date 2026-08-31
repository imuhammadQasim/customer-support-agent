"""Typed application configuration via pydantic-settings.

Environment variables use a nested delimiter, e.g. ``DB__URL``, ``LLM__ANTHROPIC_API_KEY``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    """General application settings."""

    name: str = "agentic-platform"
    env: str = "local"
    debug: bool = True
    version: str = "0.1.0"
    api_prefix: str = "/api"
    auth_disabled: bool = True  # TODO: set False once real auth is wired.
    request_timeout_s: float = 30.0


class DBConfig(BaseModel):
    """SQLAlchemy async engine settings."""

    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentic"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True


class RedisConfig(BaseModel):
    """Redis connection + session-memory settings."""

    url: str = "redis://localhost:6379/0"
    session_ttl_s: int = 3600
    max_connections: int = 20


class LLMConfig(BaseModel):
    """LLM provider + model-tier settings."""

    provider: str = "anthropic"
    anthropic_api_key: str = ""
    fast_model: str = "claude-haiku-4-5-20251001"
    balanced_model: str = "claude-sonnet-5"
    deep_model: str = "claude-opus-5"
    max_tokens: int = 2048
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
    db: DBConfig = Field(default_factory=DBConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
