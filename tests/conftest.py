"""Shared fixtures: async HTTP client + transactional DB session + stub externals."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  register model metadata
from app.api.deps import get_db, get_llm_provider, get_redis
from app.db.base import Base
from app.llm.base import ChatMessage, LLMResponse, LLMStreamChunk, ToolSpec
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


class StubLLMProvider:
    """Deterministic in-memory LLMProvider for tests."""

    async def complete(
        self,
        *,
        messages: list[ChatMessage],
        model: str,
        tools: list[ToolSpec] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        last = messages[-1].content if messages else ""
        return LLMResponse(text=f"stub:{last}", model=model)

    async def stream(
        self,
        *,
        messages: list[ChatMessage],
        model: str,
        tools: list[ToolSpec] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMStreamChunk]:
        last = messages[-1].content if messages else ""
        for token in f"stub:{last}".split():
            yield LLMStreamChunk(type="text", text=token + " ")
        yield LLMStreamChunk(type="done", stop_reason="stop")

    async def aclose(self) -> None:
        return None


class FakeRedis:
    """Minimal async Redis stand-in supporting the ops SessionMemory uses."""

    def __init__(self) -> None:
        self._lists: dict[str, list[str]] = {}

    async def rpush(self, key: str, *values: str) -> int:
        self._lists.setdefault(key, []).extend(values)
        return len(self._lists[key])

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        data = self._lists.get(key, [])
        return data[start:] if end == -1 else data[start : end + 1]

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        data = self._lists.get(key, [])
        self._lists[key] = data[start:] if end == -1 else data[start : end + 1]
        return True

    async def expire(self, key: str, ttl: int) -> bool:
        return True

    async def delete(self, *keys: str) -> int:
        return sum(1 for k in keys if self._lists.pop(k, None) is not None)

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[Any]:
    """A single-connection in-memory SQLite engine with the schema created."""
    engine = create_async_engine(
        TEST_DB_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncIterator[AsyncSession]:
    """A session wrapped in a transaction that is rolled back after each test."""
    connection = await db_engine.connect()
    trans = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    """An httpx client bound to the app with DB/Redis/LLM overridden."""

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    fake_redis = FakeRedis()
    stub_llm = StubLLMProvider()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = lambda: fake_redis
    app.dependency_overrides[get_llm_provider] = lambda: stub_llm

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
