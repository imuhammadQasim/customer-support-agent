"""SSE chat streaming endpoint tests."""

from __future__ import annotations

import httpx


async def test_chat_stream_echoes_tokens(client: httpx.AsyncClient) -> None:
    """The echo agent streams token events and a terminal done event."""
    resp = await client.post("/api/v1/sessions", json={"agent_name": "echo"})
    session_id = resp.json()["id"]

    async with client.stream(
        "POST",
        f"/api/v1/chat/{session_id}/stream",
        json={"message": "hello world"},
    ) as stream:
        assert stream.status_code == 200
        assert stream.headers["content-type"].startswith("text/event-stream")
        lines = [line async for line in stream.aiter_lines()]

    payload = "\n".join(lines)
    assert "event: token" in payload
    assert "event: done" in payload
