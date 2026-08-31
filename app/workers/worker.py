"""Background worker entrypoint.

Run with: ``uv run python -m app.workers.worker``

TODO: wire a real task queue (arq, Celery, Dramatiq, or Redis Streams) and
dispatch to app.workers.tasks.
"""

from __future__ import annotations

import asyncio

import structlog

from app.core.config import get_settings
from app.core.logging import configure_logging

logger = structlog.get_logger("app.workers.worker")


async def main() -> None:
    """Start the worker loop."""
    settings = get_settings()
    configure_logging(settings)
    logger.info("worker.start", env=settings.app.env)
    # TODO: connect to the broker and start consuming jobs.
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
