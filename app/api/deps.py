"""FastAPI dependency providers."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.chat_service import ChatService
from app.services.session_store import store

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_chat_service() -> ChatService:
    """Build the chat service once and reuse it (it holds the model client)."""
    return ChatService(store=store, settings=get_settings())


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
