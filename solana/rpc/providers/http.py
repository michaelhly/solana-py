"""HTTP RPC Provider."""
import itertools
import logging
import os
from typing import Any, Optional, cast, Union, Dict, Tuple

import requests
import httpx

from .._utils.encoding import FriendlyJsonSerde
from ..types import URI, RPCMethod, RPCResponse
from .base import BaseProvider, AsyncBaseProvider


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANARPC_HTTP_URI", "http://localhost:8899"))


class _HTTPProviderCore(FriendlyJsonSerde):
    logger = logging.getLogger("solanaweb3.rpc.httprpc.HTTPClient")

    def __init__(self, endpoint: Optional[str] = None):
        """Init."""
        self._request_counter = itertools.count()
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)
        self.health_uri = URI(f"{self.endpoint_uri}/health")

    def _build_request_kwargs(
        self, request_id: int, method: RPCMethod, params: Tuple[Any, ...], is_async: bool
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        data = self.json_encode({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        data_kwarg = "content" if is_async else "data"
        return {"url": self.endpoint_uri, "headers": headers, data_kwarg: data}

    def _increment_counter_and_get_id(self) -> int:
        return next(self._request_counter) + 1

    def _before_request(self, method: RPCMethod, params: Tuple[Any, ...], is_async: bool) -> Dict[str, Any]:
        request_id = self._increment_counter_and_get_id()
        self.logger.debug(
            "Making HTTP request. URI: %s, RequestID: %d, Method: %s, Params: %s",
            self.endpoint_uri,
            request_id,
            method,
            params,
        )
        return self._build_request_kwargs(request_id=request_id, method=method, params=params, is_async=is_async)

    def _after_request(self, raw_response: Union[requests.Response, httpx.Response], method: RPCMethod) -> RPCResponse:
        raw_response.raise_for_status()
        self.logger.debug(
            "Getting response HTTP. URI: %s, " "Method: %s, Response: %s", self.endpoint_uri, method, raw_response.text
        )
        return cast(RPCResponse, self.json_decode(raw_response.text))


class HTTPProvider(BaseProvider, _HTTPProviderCore):
    """HTTP provider to interact with the http rpc endpoint."""

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"HTTP RPC connection {self.endpoint_uri}"

    def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make an HTTP request to an http rpc endpoint."""
        request_kwargs = self._before_request(method=method, params=params, is_async=False)
        raw_response = requests.post(**request_kwargs)
        return self._after_request(raw_response=raw_response, method=method)

    def is_connected(self) -> bool:
        """Health check."""
        try:
            response = requests.get(self.health_uri)
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:
            self.logger.error("Health check failed with error: %s", str(err))
            return False

        return response.ok


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
