"""Redis-list-backed implementation of :class:`SessionMemory`."""

from __future__ import annotations

from redis.asyncio import Redis

from app.agents.memory.base import MemoryTurn, SessionMemory


class RedisSessionMemory(SessionMemory):
    """Stores conversation history as a capped, TTL'd Redis list."""

    def __init__(
        self,
        redis: Redis,
        session_id: str,
        *,
        ttl_s: int = 3600,
        max_turns: int = 200,
    ) -> None:
        self._redis = redis
        self._session_id = session_id
        self._ttl_s = ttl_s
        self._max_turns = max_turns

    @property
    def key(self) -> str:
        """Redis key holding this session's history list."""
        return f"session:{self._session_id}:history"

    async def append(self, turn: MemoryTurn) -> None:
        """Append a turn, trim to ``max_turns``, and refresh the TTL."""
        await self._redis.rpush(self.key, turn.model_dump_json())
        await self._redis.ltrim(self.key, -self._max_turns, -1)
        await self._redis.expire(self.key, self._ttl_s)

    async def get_history(self, *, limit: int | None = None) -> list[MemoryTurn]:
        """Return stored turns, oldest first."""
        raw = await self._redis.lrange(self.key, 0, -1)
        turns = [MemoryTurn.model_validate_json(item) for item in raw]
        return turns[-limit:] if limit is not None else turns

    async def clear(self) -> None:
        """Delete the history list."""
        await self._redis.delete(self.key)
