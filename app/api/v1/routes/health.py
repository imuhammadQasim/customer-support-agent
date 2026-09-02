"""Liveness endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.deps import SettingsDep

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: SettingsDep) -> dict[str, Any]:
    """Liveness probe: the process is up."""
    return {
        "status": "ok",
        "service": settings.app.name,
        "version": settings.app.version,
        "env": settings.app.env,
    }
