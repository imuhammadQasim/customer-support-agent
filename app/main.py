"""Application entrypoint: builds and exposes the FastAPI app."""

from __future__ import annotations

import structlog
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import add_exception_handlers
from app.core.logging import configure_logging, request_context_middleware

logger = structlog.get_logger("app.main")


def create_app() -> FastAPI:
    """Construct the FastAPI application with middleware, handlers, and routes."""
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # Request-id + timing (see app/core/logging.py).
    app.middleware("http")(request_context_middleware)

    # Consistent JSON error envelope for AppError + framework errors.
    add_exception_handlers(app)

    # Versioned API under the configured prefix, e.g. /api/v1/...
    app.include_router(api_router, prefix=settings.app.api_prefix)

    logger.info("app.created", version=settings.app.version, env=settings.app.env)
    return app


app = create_app()
