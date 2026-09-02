"""CRUD endpoints for conversation sessions and their messages."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.session import MessageRead, SessionCreate, SessionRead
from app.services.session_store import store

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate | None = None) -> SessionRead:
    """Open a new (empty) session. Body is optional: ``{"title": "..."}``."""
    title = payload.title if payload else None
    return SessionRead.of(store.create(title=title))


@router.get("", response_model=list[SessionRead])
async def list_sessions() -> list[SessionRead]:
    """List all sessions."""
    return [SessionRead.of(s) for s in store.list()]


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(session_id: str) -> SessionRead:
    """Fetch a single session by id."""
    return SessionRead.of(store.get(session_id))


@router.get("/{session_id}/messages", response_model=list[MessageRead])
async def list_messages(session_id: str) -> list[MessageRead]:
    """List a session's messages, oldest first."""
    return [MessageRead.of(m) for m in store.get(session_id).messages]


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str) -> None:
    """Delete a session and its messages."""
    store.delete(session_id)
