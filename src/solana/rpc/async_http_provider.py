"""Async HTTP RPC Provider."""

from __future__ import annotations

import logging
import os
from typing import Any, TypeVar

import httpx2
from aiolimiter import AsyncLimiter
from solders.rpc.requests import Body
from solders.rpc.responses import RPCError, RPCResult

from ..exceptions import SolanaRpcException, handle_async_exceptions
from .core import RPCException
from .jsonrpc import JsonRpcRequestSerializer
from .types import URI

T = TypeVar("T", bound=RPCResult)

DEFAULT_MAX_TRANSPORT_RETRIES = 1
_RETRYABLE_TRANSPORT_EXCEPTIONS = (httpx2.TransportError,)


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANARPC_HTTP_URI", "http://localhost:8899"))


class AsyncHTTPProvider:
    """Async HTTP provider to interact with the http rpc endpoint."""

    logger = logging.getLogger("solana.rpc.async_http_provider")

    def __init__(
        self,
        endpoint: str | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: float | None = None,
        proxy: str | None = None,
        rate_limit: float = 0,
        max_connections: int | None = None,
        max_keepalive_connections: int | None = None,
        keepalive_expiry: float | None = None,
        http2: bool = True,
        max_transport_retries: int = DEFAULT_MAX_TRANSPORT_RETRIES,
    ):
        """Init AsyncHTTPProvider.

        Args:
            endpoint: URL of the RPC endpoint.
            extra_headers: Extra headers to pass for HTTP request.
            timeout: HTTP request timeout in seconds. ``None`` uses the httpx2 default.
            proxy: Proxy URL to pass to the HTTP client.
            rate_limit: Maximum requests per second. ``0`` (default) disables rate limiting.
            max_connections: Maximum number of concurrent connections. ``None`` uses the httpx2 default.
            max_keepalive_connections: Maximum number of idle keep-alive connections. ``None`` uses the
                httpx2 default.
            keepalive_expiry: Idle keep-alive connection expiry in seconds. ``None`` uses the httpx2
                default.
            http2: Enable HTTP/2 support.
            max_transport_retries: Maximum number of times to retry httpx2 transport errors.
        """
        if max_transport_retries < 0:
            raise ValueError("max_transport_retries must be non-negative")
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)
        self.timeout = timeout
        self.extra_headers = extra_headers
        self._max_transport_retries = max_transport_retries
        client_kwargs: dict[str, Any] = {"http2": http2}
        if timeout is not None:
            client_kwargs["timeout"] = httpx2.Timeout(timeout)
        if proxy is not None:
            client_kwargs["proxy"] = proxy
        if any(
            value is not None
            for value in (
                max_connections,
                max_keepalive_connections,
                keepalive_expiry,
            )
        ):
            client_kwargs["limits"] = httpx2.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
                keepalive_expiry=keepalive_expiry,
            )
        self.session = httpx2.AsyncClient(**client_kwargs)
        self._limiter: AsyncLimiter | None = AsyncLimiter(rate_limit, time_period=1) if rate_limit > 0 else None

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"Async HTTP RPC connection {self.endpoint_uri}"

    @handle_async_exceptions(SolanaRpcException, httpx2.HTTPError)
    async def make_request(self, body: Body, parser: type[T]) -> T:
        """Make an async HTTP request to an http rpc endpoint."""
        raw = await self.make_request_unparsed(body)
        return _parse_raw(raw, parser=parser)

    @handle_async_exceptions(SolanaRpcException, httpx2.HTTPError)
    async def make_request_unparsed(self, body: JsonRpcRequestSerializer) -> str:
        """Make an async HTTP request to an http rpc endpoint."""
        headers = {"Content-Type": "application/json"}
        if self.extra_headers:
            headers.update(self.extra_headers)
        raw_response = await self._post_request(body.to_json(), headers)
        return _after_request_unparsed(raw_response)

    async def _post_request(self, content: str, headers: dict[str, str]) -> httpx2.Response:
        retries_left = self._max_transport_retries
        while True:
            try:
                return await self._post_request_once(content, headers)
            except _RETRYABLE_TRANSPORT_EXCEPTIONS as exc:
                if retries_left <= 0:
                    raise
                retries_left -= 1
                self.logger.debug(
                    "Retrying HTTP RPC request after %s: %s",
                    exc.__class__.__name__,
                    exc,
                )

    async def _post_request_once(self, content: str, headers: dict[str, str]) -> httpx2.Response:
        if self._limiter is not None:
            async with self._limiter:
                return await self.session.post(self.endpoint_uri, content=content, headers=headers)
        return await self.session.post(self.endpoint_uri, content=content, headers=headers)

    async def __aenter__(self) -> AsyncHTTPProvider:
        """Use as a context manager."""
        await self.session.__aenter__()
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        """Exits the context manager."""
        await self.close()

    async def close(self) -> None:
        """Close session."""
        await self.session.aclose()


def _parse_raw(raw: str, parser: type[T]) -> T:
    parsed = parser.from_json(raw)  # type: ignore
    if isinstance(parsed, RPCError.__args__):  # type: ignore # TODO: drop py37 and use typing.get_args
        raise RPCException(parsed)
    return parsed  # type: ignore


def _after_request_unparsed(raw_response: httpx2.Response) -> str:
    raw_response.raise_for_status()
    return raw_response.text
