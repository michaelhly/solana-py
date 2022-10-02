"""HTTP RPC Provider."""
from typing import Type
import requests
from solders.rpc.requests import Body

from ...exceptions import SolanaRpcException, handle_exceptions
from ..types import RPCResponse
from .base import BaseProvider
from .core import _HTTPProviderCore, T, _after_request, _after_request_raw


class HTTPProvider(BaseProvider, _HTTPProviderCore):
    """HTTP provider to interact with the http rpc endpoint."""

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"HTTP RPC connection {self.endpoint_uri}"

    @handle_exceptions(SolanaRpcException, requests.exceptions.RequestException)
    def make_request_raw(self, body: Body) -> str:
        """Make an HTTP request to an http rpc endpoint."""
        request_kwargs = self._build_request_kwargs(body, is_async=False)
        raw_response = requests.post(**request_kwargs, timeout=self.timeout)
        return _after_request_raw(raw_response=raw_response)

    @handle_exceptions(SolanaRpcException, requests.exceptions.RequestException)
    def make_request(self, body: Body, parser: Type[T]) -> T:
        """Make an HTTP request to an http rpc endpoint."""
        request_kwargs = self._build_request_kwargs(body, is_async=False)
        raw_response = requests.post(**request_kwargs, timeout=self.timeout)
        return _after_request(raw_response=raw_response, parser=parser)

    def is_connected(self) -> bool:
        """Health check."""
        try:
            response = requests.get(self.health_uri)
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:
            self.logger.error("Health check failed with error: %s", str(err))
            return False

        return response.ok
