"""Authentication / authorization primitives (skeleton)."""

from __future__ import annotations

import hashlib
import hmac
from typing import Annotated

from fastapi import Header
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import AppError


class AuthError(AppError):
    """Raised when a caller cannot be authenticated."""

    status_code = 401
    code = "unauthorized"

    def __init__(self, message: str = "Unauthorized", **kwargs: object) -> None:
        super().__init__(message, **kwargs)  # type: ignore[arg-type]


class Principal(BaseModel):
    """The authenticated caller."""

    subject: str
    scopes: list[str] = []


def hash_secret(secret: str, *, salt: str) -> str:
    """Derive a storable hash from a secret.

    TODO: replace PBKDF2 with argon2id (e.g. via ``argon2-cffi`` / ``passlib``).
    """
    return hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), 100_000).hex()


def verify_secret(secret: str, hashed: str, *, salt: str) -> bool:
    """Constant-time comparison of a candidate secret against a stored hash."""
    return hmac.compare_digest(hash_secret(secret, salt=salt), hashed)


async def get_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    """FastAPI dependency: resolve the caller's :class:`Principal`."""
    settings = get_settings()
    if settings.app.auth_disabled:
        return Principal(subject="anonymous", scopes=["*"])

    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("Missing or malformed Authorization header.")

    _token = authorization.split(" ", 1)[1]
    # TODO: verify token (JWT signature / introspection / API-key lookup) and load scopes.
    raise AuthError("Token verification is not implemented.")
