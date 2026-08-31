"""FastAPI dependency providers. This is the only place services get wired."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.memory.redis_memory import RedisSessionMemory
from app.agents.runtime import AgentRuntime
from app.agents.tools.registry import ToolRegistry
from app.core.config import Settings, get_settings
from app.core.lifespan import AppResources
from app.llm.base import LLMProvider
from app.llm.router import LLMRouter
from app.repositories.message import MessageRepository
from app.repositories.session import SessionRepository
from app.services.chat_service import ChatService
from app.services.session_service import SessionService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_resources(request: Request) -> AppResources:
    """Return the live :class:`AppResources` created by the lifespan."""
    resources: AppResources | None = getattr(request.app.state, "resources", None)
    if resources is None:  # pragma: no cover - misconfiguration only
        raise RuntimeError("AppResources missing; did the app lifespan run?")
    return resources


ResourcesDep = Annotated[AppResources, Depends(get_resources)]


async def get_db(resources: ResourcesDep) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async DB session, committing on success."""
    async with resources.sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DBDep = Annotated[AsyncSession, Depends(get_db)]


def get_redis(resources: ResourcesDep) -> Redis:
    """Return the shared Redis client."""
    return resources.redis


RedisDep = Annotated[Redis, Depends(get_redis)]


def get_llm_provider(resources: ResourcesDep) -> LLMProvider:
    """Return the shared LLM provider."""
    return resources.llm


LLMDep = Annotated[LLMProvider, Depends(get_llm_provider)]


def get_session_repository(db: DBDep) -> SessionRepository:
    """Construct a :class:`SessionRepository` bound to the request session."""
    return SessionRepository(db)


def get_message_repository(db: DBDep) -> MessageRepository:
    """Construct a :class:`MessageRepository` bound to the request session."""
    return MessageRepository(db)


def get_session_service(
    session_repo: Annotated[SessionRepository, Depends(get_session_repository)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> SessionService:
    """Assemble the session service."""
    return SessionService(session_repo=session_repo, message_repo=message_repo)


def get_chat_service(
    settings: SettingsDep,
    llm: LLMDep,
    redis: RedisDep,
    session_repo: Annotated[SessionRepository, Depends(get_session_repository)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repository)],
) -> ChatService:
    """Assemble the chat service and its agent runtime."""
    runtime = AgentRuntime(
        llm_router=LLMRouter(llm, settings),
        tool_registry=ToolRegistry.default(),
        memory_factory=lambda session_id: RedisSessionMemory(
            redis, session_id, ttl_s=settings.redis.session_ttl_s
        ),
        settings=settings,
    )
    return ChatService(session_repo=session_repo, message_repo=message_repo, runtime=runtime)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
