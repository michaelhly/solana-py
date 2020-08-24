"""Client to interact with the Solana JSON RPC HTTP Endpoint."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional, cast
from uuid import uuid4

import requests

from solanarpc._utils.encoding import FriendlyJsonSerde
from solanarpc.rpc_types import RPCMethod, RPCResponse, URI


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANAWEB3_HTTP_URI", "http://localhost:8899"))


class HTTPClient:
    """HTTP client interact with the http rpc endpoint."""

    logger = logging.getLogger("solanaweb3.rpc.httprpc.HTTPClient")

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)

    def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make an HTTP reqeust to the http rpc endpoint."""
        request_id = uuid4().int
        self.logger.debug(
            "Making HTTP request. RequestID: %d, URI: %s, Method: %s", request_id, self.endpoint_uri, method
        )
        headers = {"Content-Type": "application/json"}
        data = FriendlyJsonSerde().json_encode({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        raw_response = requests.post(self.endpoint_uri, headers=headers, data=data)
        raw_response.raise_for_status()
        self.logger.debug(
            "Getting response HTTP. URI: %s, " "Method: %s, Response: %s", self.endpoint_uri, method, raw_response.text
        )
        return cast(RPCResponse, FriendlyJsonSerde.json_decode(raw_response.text))

    def send_transaction(self, signed_tx: bytes) -> RPCResponse:
        """Submits a signed transaction to the cluster for processing.

        :param signed_tx: fully-signed Transaction, as base-58 encoded bytes string.
        """
        return self.make_request(RPCMethod("sendTransaction"), signed_tx)
