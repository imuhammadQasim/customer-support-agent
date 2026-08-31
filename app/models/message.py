"""Message model: a single turn within a session."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.session import Session


class Message(UUIDMixin, TimestampMixin, Base):
    """A single conversation turn."""

    __tablename__ = "messages"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text, default="")
    token_count: Mapped[int | None] = mapped_column(Integer, default=None)
    tool_calls: Mapped[list[Any] | None] = mapped_column(JSON, default=None)

    session: Mapped["Session"] = relationship(back_populates="messages")
