"""HTTP RPC Provider."""
from typing import Any

import requests

from ..types import RPCMethod, RPCResponse
from .base import BaseProvider
from .core import _HTTPProviderCore


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
