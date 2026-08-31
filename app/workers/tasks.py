"""Task functions executed by the background worker."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger("app.workers.tasks")


async def run_agent_job(payload: dict[str, Any]) -> None:
    """Execute a long-running agent turn off the request path.

    TODO:
      - pull session_id / message / agent_name from ``payload``
      - build an AgentRuntime the same way app.api.deps.get_chat_service does
      - consume runtime.stream(...) and persist messages + usage
    """
    logger.info("worker.job.received", keys=sorted(payload))
    raise NotImplementedError
