"""HTTP RPC Provider."""
import itertools
import logging
import os
from typing import Any, Optional, cast

import requests

from .._utils.encoding import FriendlyJsonSerde
from ..types import URI, RPCMethod, RPCResponse
from .base import BaseProvider


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANARPC_HTTP_URI", "http://localhost:8899"))


class HTTPProvider(BaseProvider, FriendlyJsonSerde):
    """HTTP provider interact with the http rpc endpoint."""

    logger = logging.getLogger("solanaweb3.rpc.httprpc.HTTPClient")

    def __init__(self, endpoint: Optional[str] = None):
        """Init HTTPProvider."""
        self._request_counter = itertools.count()
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"HTTP RPC connection {self.endpoint_uri}"

    def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make an HTTP request to an http rpc endpoint."""
        request_id = next(self._request_counter) + 1
        self.logger.debug(
            "Making HTTP request. URI: %s, RequestID: %d, Method: %s, Params: %s",
            self.endpoint_uri,
            request_id,
            method,
            params,
        )
        headers = {"Content-Type": "application/json"}
        data = self.json_encode({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        raw_response = requests.post(self.endpoint_uri, headers=headers, data=data)
        raw_response.raise_for_status()
        self.logger.debug(
            "Getting response HTTP. URI: %s, " "Method: %s, Response: %s", self.endpoint_uri, method, raw_response.text
        )
        return cast(RPCResponse, self.json_decode(raw_response.text))

    def is_connected(self) -> bool:
        """Health check."""
        try:
            response = requests.get(f"{self.endpoint_uri}/health")
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:
            self.logger.error("Health check failed with error: %s", str(err))
            return False

        return response.ok
