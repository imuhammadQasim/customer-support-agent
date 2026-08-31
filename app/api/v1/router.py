"""Aggregate v1 route modules under a single router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import chat, health, sessions

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health.router)
v1_router.include_router(sessions.router)
v1_router.include_router(chat.router)

api_router = APIRouter()
api_router.include_router(v1_router)
