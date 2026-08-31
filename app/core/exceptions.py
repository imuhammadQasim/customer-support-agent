"""Application error hierarchy + consistent JSON error-envelope handlers."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger("app.errors")


class AppError(Exception):
    """Base class for all expected application errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "Internal server error", *, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    """A requested resource does not exist."""

    status_code = 404
    code = "not_found"

    def __init__(self, message: str = "Resource not found", *, details: Any | None = None) -> None:
        super().__init__(message, details=details)


class ValidationError(AppError):
    """Domain-level validation failure (distinct from request-body validation)."""

    status_code = 422
    code = "validation_error"

    def __init__(self, message: str = "Validation failed", *, details: Any | None = None) -> None:
        super().__init__(message, details=details)


class ToolExecutionError(AppError):
    """A tool invoked by an agent failed."""

    status_code = 502
    code = "tool_execution_error"

    def __init__(self, message: str = "Tool execution failed", *, details: Any | None = None) -> None:
        super().__init__(message, details=details)


class LLMError(AppError):
    """The LLM provider returned an error or was unreachable."""

    status_code = 502
    code = "llm_error"

    def __init__(self, message: str = "LLM provider error", *, details: Any | None = None) -> None:
        super().__init__(message, details=details)


def _request_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID") or getattr(request.state, "request_id", None)


def _envelope(*, code: str, message: str, details: Any | None, request_id: str | None) -> dict[str, Any]:
    """Build the canonical error response body."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle known :class:`AppError` subclasses."""
    logger.warning("app_error", code=exc.code, message=exc.message, status_code=exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(
            code=exc.code,
            message=exc.message,
            details=jsonable_encoder(exc.details),
            request_id=_request_id(request),
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI request-body/query validation errors."""
    return JSONResponse(
        status_code=422,
        content=_envelope(
            code="validation_error",
            message="Request validation failed",
            details=jsonable_encoder(exc.errors()),
            request_id=_request_id(request),
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle raw Starlette/FastAPI HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(
            code="http_error",
            message=str(exc.detail),
            details=None,
            request_id=_request_id(request),
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions."""
    logger.exception("unhandled_error")
    return JSONResponse(
        status_code=500,
        content=_envelope(
            code="internal_error",
            message="Internal server error",
            details=None,
            request_id=_request_id(request),
        ),
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the app."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
