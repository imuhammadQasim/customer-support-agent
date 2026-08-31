"""CRUD endpoints for conversation sessions and their messages."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api.deps import SessionServiceDep
from app.schemas.common import Page
from app.schemas.session import MessageRead, SessionCreate, SessionRead

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate, service: SessionServiceDep) -> SessionRead:
    """Create a new session bound to an agent."""
    session = await service.create_session(payload)
    return SessionRead.model_validate(session)


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(session_id: str, service: SessionServiceDep) -> SessionRead:
    """Fetch a single session by id."""
    session = await service.get_session(session_id)
    return SessionRead.model_validate(session)


@router.get("/{session_id}/messages", response_model=Page[MessageRead])
async def list_messages(
    session_id: str,
    service: SessionServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[MessageRead]:
    """List messages for a session, oldest first."""
    messages = await service.list_messages(session_id, limit=limit, offset=offset)
    return Page[MessageRead](
        items=[MessageRead.model_validate(m) for m in messages],
        limit=limit,
        offset=offset,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, service: SessionServiceDep) -> None:
    """Delete a session and its messages."""
    await service.delete_session(session_id)
