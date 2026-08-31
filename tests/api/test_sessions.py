"""Session CRUD endpoint tests."""

from __future__ import annotations

import httpx


async def test_session_crud(client: httpx.AsyncClient) -> None:
    """Create -> read -> list messages -> delete."""
    resp = await client.post("/api/v1/sessions", json={"agent_name": "echo"})
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/sessions/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["agent_name"] == "echo"

    resp = await client.get(f"/api/v1/sessions/{session_id}/messages")
    assert resp.status_code == 200
    assert resp.json()["items"] == []

    resp = await client.delete(f"/api/v1/sessions/{session_id}")
    assert resp.status_code == 204


async def test_get_missing_session_returns_error_envelope(client: httpx.AsyncClient) -> None:
    """Unknown session ids produce the canonical error envelope."""
    resp = await client.get("/api/v1/sessions/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
