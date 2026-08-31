"""Shared schema building blocks."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ItemT = TypeVar("ItemT")


class ORMModel(BaseModel):
    """Base for schemas read directly from ORM instances."""

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Body of the canonical error envelope."""

    code: str
    message: str
    details: Any | None = None
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    """Consistent error response shape returned by all handlers."""

    error: ErrorDetail


class Page(BaseModel, Generic[ItemT]):
    """A simple offset-paginated result set."""

    items: list[ItemT]
    total: int | None = None
    limit: int = 50
    offset: int = 0


class PaginationParams(BaseModel):
    """Reusable pagination query params."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
