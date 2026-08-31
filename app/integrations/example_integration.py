"""Reference integration wrapping an outbound HTTP API."""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.base import BaseIntegration


class ExampleHTTPIntegration(BaseIntegration):
    """Demonstrates the integration pattern against a generic HTTP service."""

    name = "example"

    def __init__(self, base_url: str, *, timeout_s: float = 10.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_s)

    async def healthcheck(self) -> bool:
        """Ping the remote health endpoint."""
        # TODO: call a real endpoint and inspect the response.
        return True

    async def fetch_resource(self, resource_id: str) -> dict[str, Any]:
        """Fetch a single resource by id."""
        # TODO: implement request + map transport/HTTP errors to app errors.
        raise NotImplementedError

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
