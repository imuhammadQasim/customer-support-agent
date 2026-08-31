"""Session model: a conversation bound to a single agent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.message import Message


class Session(UUIDMixin, TimestampMixin, Base):
    """A conversation session."""

    __tablename__ = "sessions"

    user_id: Mapped[str | None] = mapped_column(String(255), index=True, default=None)
    agent_name: Mapped[str] = mapped_column(String(128), default="echo")
    status: Mapped[str] = mapped_column(String(32), default="active")
    title: Mapped[str | None] = mapped_column(String(255), default=None)
    # 'metadata' is reserved on the declarative base, so store under a distinct column.
    meta: Mapped[dict[str, Any]] = mapped_column("metadata_json", JSON, default=dict)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
