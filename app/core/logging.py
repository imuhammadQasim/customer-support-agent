"""structlog JSON logging config + request-context middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

import structlog
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.utils.ids import new_request_id

REQUEST_ID_HEADER = "X-Request-ID"

_ASGIApp = Callable[[Request], Awaitable[Response]]


def configure_logging(settings: Settings) -> None:
    """Configure structlog to emit one JSON object per line on stdout."""
    level = logging.DEBUG if settings.app.debug else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger("app.request")


async def request_context_middleware(request: Request, call_next: _ASGIApp) -> Response:
    """Generate/propagate a request id, bind it into structlog, and time the request."""
    request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
    request.state.request_id = request_id

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request.error",
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        raise

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers[REQUEST_ID_HEADER] = request_id
    logger.info("request.complete", status_code=response.status_code, elapsed_ms=elapsed_ms)
    structlog.contextvars.clear_contextvars()
    return response
