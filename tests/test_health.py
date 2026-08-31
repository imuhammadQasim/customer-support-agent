"""Health endpoint tests."""

from __future__ import annotations

import httpx


async def test_health_ok(client: httpx.AsyncClient) -> None:
    """GET /api/v1/health returns a 200 with status 'ok'."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
