"""Async HTTP RPC Provider."""

from __future__ import annotations

from typing import Dict, Optional, Type

import httpx2
from aiolimiter import AsyncLimiter
from solders.rpc.requests import Body

from ...exceptions import SolanaRpcException, handle_async_exceptions
from .async_base import AsyncBaseProvider
from .core import (
    DEFAULT_LIMITS,
    DEFAULT_TIMEOUT,
    T,
    _after_request_unparsed,
    _HTTPProviderCore,
    _parse_raw,
)


class AsyncHTTPProvider(AsyncBaseProvider, _HTTPProviderCore):
    """Async HTTP provider to interact with the http rpc endpoint."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT,
        proxy: Optional[str] = None,
        rate_limit: float = 0,
    ):
        """Init AsyncHTTPProvider.

        Args:
            endpoint: URL of the RPC endpoint.
            extra_headers: Extra headers to pass for HTTP request.
            timeout: HTTP request timeout in seconds.
            proxy: Proxy URL to pass to the HTTP client.
            rate_limit: Maximum requests per second. ``0`` (default) disables rate limiting.
        """
        super().__init__(endpoint, extra_headers)
        if proxy is None:
            self.session = httpx2.AsyncClient(
                timeout=timeout,
                limits=DEFAULT_LIMITS,
            )
        else:
            self.session = httpx2.AsyncClient(timeout=timeout, proxy=proxy, limits=DEFAULT_LIMITS)
        self._limiter: Optional[AsyncLimiter] = AsyncLimiter(rate_limit, time_period=1) if rate_limit > 0 else None

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"Async HTTP RPC connection {self.endpoint_uri}"

    @handle_async_exceptions(SolanaRpcException, httpx2.HTTPError)
    async def make_request(self, body: Body, parser: Type[T]) -> T:
        """Make an async HTTP request to an http rpc endpoint."""
        raw = await self.make_request_unparsed(body)
        return _parse_raw(raw, parser=parser)

    async def make_request_unparsed(self, body: Body) -> str:
        """Make an async HTTP request to an http rpc endpoint."""
        if self._limiter is not None:
            async with self._limiter:
                request_kwargs = self._before_request(body=body)
                try:
                    raw_response = await self.session.post(**request_kwargs)
                except (httpx2.RemoteProtocolError, httpx2.ReadError):
                    raw_response = await self.session.post(**request_kwargs)
                return _after_request_unparsed(raw_response)
        request_kwargs = self._before_request(body=body)
        try:
            raw_response = await self.session.post(**request_kwargs)
        except (httpx2.RemoteProtocolError, httpx2.ReadError):
            # httpcore2 does not auto-retry stale keepalive connections (unlike httpcore 1.x).
            # Also retry on ReadError (ECONNRESET) which occurs when the server forcibly
            # closes the connection mid-response under load.
            raw_response = await self.session.post(**request_kwargs)
        return _after_request_unparsed(raw_response)

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
