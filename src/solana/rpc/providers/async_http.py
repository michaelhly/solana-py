"""Async HTTP RPC Provider."""
from typing import Any, Optional

import httpx

from ..types import RPCMethod, RPCResponse
from .async_base import AsyncBaseProvider
from .core import _HTTPProviderCore


class AsyncHTTPProvider(AsyncBaseProvider, _HTTPProviderCore):
    """Async HTTP provider to interact with the http rpc endpoint."""

    def __init__(self, endpoint: Optional[str] = None):
        """Init AsyncHTTPProvider."""
        super().__init__(endpoint)
        self.session = httpx.AsyncClient()

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"Async HTTP RPC connection {self.endpoint_uri}"

    async def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make an async HTTP request to an http rpc endpoint."""
        request_kwargs = self._before_request(method=method, params=params, is_async=True)
        raw_response = await self.session.post(**request_kwargs)
        return self._after_request(raw_response=raw_response, method=method)

    async def is_connected(self) -> bool:
        """Health check."""
        try:
            response = await self.session.get(self.health_uri)
            response.raise_for_status()
        except (IOError, httpx.HTTPError) as err:
            self.logger.error("Health check failed with error: %s", str(err))
            return False

        return response.status_code == httpx.codes.OK

    async def __aenter__(self) -> "AsyncHTTPProvider":
        """Use as a context manager."""
        await self.session.__aenter__()
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        """Exits the context manager."""
        await self.close()

    async def close(self) -> None:
        """Close session."""
        await self.session.aclose()
