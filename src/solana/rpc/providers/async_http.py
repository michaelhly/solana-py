"""Async HTTP RPC Provider."""

from __future__ import annotations

import logging
import os
from typing import Optional, Type, TypeVar

import httpx2
from aiolimiter import AsyncLimiter
from solders.rpc.requests import Body
from solders.rpc.responses import RPCError, RPCResult

from ...exceptions import SolanaRpcException, handle_async_exceptions
from ..core import RPCException
from ..jsonrpc import JsonRpcRequestSerializer
from ..types import URI

DEFAULT_TIMEOUT = 10
# httpcore2 2.x no longer auto-retries dropped connections (unlike httpcore 1.x).
# RemoteProtocolError (stale keepalive) and ReadError (ECONNRESET) are both retried
# once explicitly in the provider layer.
# We keep the pool small (single-endpoint RPC client) but leave keepalive_expiry at the
# httpx2 default so long-running clients don't reconnect unnecessarily.
DEFAULT_LIMITS = httpx2.Limits(max_connections=10, max_keepalive_connections=5)

T = TypeVar("T", bound=RPCResult)


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANARPC_HTTP_URI", "http://localhost:8899"))


class AsyncHTTPProvider:
    """Async HTTP provider to interact with the http rpc endpoint."""

    logger = logging.getLogger("solana.rpc.providers")

    def __init__(
        self,
        endpoint: Optional[str] = None,
        extra_headers: Optional[dict[str, str]] = None,
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
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)
        self.timeout = timeout
        self.extra_headers = extra_headers
        if proxy is None:
            self.session = httpx2.AsyncClient(
                timeout=timeout,
                limits=DEFAULT_LIMITS,
            )
        else:
            self.session = httpx2.AsyncClient(
                timeout=timeout, proxy=proxy, limits=DEFAULT_LIMITS
            )
        self._limiter: Optional[AsyncLimiter] = (
            AsyncLimiter(rate_limit, time_period=1) if rate_limit > 0 else None
        )

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"Async HTTP RPC connection {self.endpoint_uri}"

    @handle_async_exceptions(SolanaRpcException, httpx2.HTTPError)
    async def make_request(self, body: Body, parser: Type[T]) -> T:
        """Make an async HTTP request to an http rpc endpoint."""
        raw = await self.make_request_unparsed(body)
        return _parse_raw(raw, parser=parser)

    @handle_async_exceptions(SolanaRpcException, httpx2.HTTPError)
    async def make_request_unparsed(self, body: JsonRpcRequestSerializer) -> str:
        """Make an async HTTP request to an http rpc endpoint."""
        headers = {"Content-Type": "application/json"}
        if self.extra_headers:
            headers.update(self.extra_headers)
        if self._limiter is not None:
            async with self._limiter:
                raw_response = await self._post_request(body, headers)
                return _after_request_unparsed(raw_response)
        raw_response = await self._post_request(body, headers)
        return _after_request_unparsed(raw_response)

    async def _post_request(
        self, body: JsonRpcRequestSerializer, headers: dict[str, str]
    ) -> httpx2.Response:
        try:
            return await self.session.post(
                self.endpoint_uri, content=body.to_json(), headers=headers
            )
        except (httpx2.RemoteProtocolError, httpx2.ReadError):
            # httpcore2 does not auto-retry stale keepalive connections (unlike httpcore 1.x).
            # Also retry on ReadError (ECONNRESET) which occurs when the server forcibly
            # closes the connection mid-response under load.
            return await self.session.post(
                self.endpoint_uri, content=body.to_json(), headers=headers
            )

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


def _parse_raw(raw: str, parser: Type[T]) -> T:
    parsed = parser.from_json(raw)  # type: ignore
    if isinstance(parsed, RPCError.__args__):  # type: ignore # TODO: drop py37 and use typing.get_args
        raise RPCException(parsed)
    return parsed  # type: ignore


def _after_request_unparsed(raw_response: httpx2.Response) -> str:
    raw_response.raise_for_status()
    return raw_response.text
