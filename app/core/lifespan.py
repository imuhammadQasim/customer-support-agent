"""Async lifespan: open/close the DB pool, Redis pool, and the LLM client."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import structlog
from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.db.session import build_engine, build_sessionmaker
from app.llm.anthropic_client import AnthropicProvider
from app.llm.base import LLMProvider

logger = structlog.get_logger("app.lifespan")


@dataclass(slots=True)
class AppResources:
    """Live singletons owned by the app for its whole lifetime."""

    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    redis: Redis
    llm: LLMProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    """Instantiate the configured LLM provider."""
    # TODO: dispatch on settings.llm.provider when more providers are added.
    return AnthropicProvider(
        api_key=settings.llm.anthropic_api_key,
        timeout_s=settings.llm.timeout_s,
        max_tokens=settings.llm.max_tokens,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup/shutdown of shared resources; wired via FastAPI(lifespan=...)."""
    settings = get_settings()
    logger.info("startup.begin", env=settings.app.env)

    engine = build_engine(settings)
    sessionmaker = build_sessionmaker(engine)
    redis: Redis = Redis.from_url(
        settings.redis.url,
        decode_responses=True,
        max_connections=settings.redis.max_connections,
    )
    llm = build_llm_provider(settings)

    app.state.resources = AppResources(
        settings=settings,
        engine=engine,
        sessionmaker=sessionmaker,
        redis=redis,
        llm=llm,
    )
    # TODO: optionally ping DB + Redis here and fail fast on startup.
    logger.info("startup.complete")

    try:
        yield
    finally:
        logger.info("shutdown.begin")
        await llm.aclose()
        await redis.aclose()
        await engine.dispose()
        logger.info("shutdown.complete")
