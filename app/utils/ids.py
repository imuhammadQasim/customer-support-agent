"""Identifier generation helpers."""

from __future__ import annotations

import uuid


def new_uuid() -> str:
    """Return a random UUID4 as a canonical string."""
    return str(uuid.uuid4())


def new_request_id() -> str:
    """Return a compact (hex) request id."""
    return uuid.uuid4().hex
