"""Async engine + sessionmaker factories."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    """Create the async SQLAlchemy engine from settings."""
    kwargs: dict[str, object] = {
        "echo": settings.db.echo,
        "pool_pre_ping": settings.db.pool_pre_ping,
    }
    # Pool sizing options are not valid for every dialect (e.g. sqlite).
    if not settings.db.url.startswith("sqlite"):
        kwargs["pool_size"] = settings.db.pool_size
        kwargs["max_overflow"] = settings.db.max_overflow
    return create_async_engine(settings.db.url, **kwargs)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an ``async_sessionmaker`` bound to ``engine``."""
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
