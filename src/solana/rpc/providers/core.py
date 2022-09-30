"""Helper code for HTTP provider classes."""
import itertools
import logging
import os
from typing import Any, Dict, Optional, Union, cast
from solders.rpc.requests import Body

import httpx
import requests

from .._utils.encoding import FriendlyJsonSerde
from ..types import URI, RPCResponse

DEFAULT_TIMEOUT = 10


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANARPC_HTTP_URI", "http://localhost:8899"))


class _HTTPProviderCore(FriendlyJsonSerde):
    logger = logging.getLogger("solanaweb3.rpc.httprpc.HTTPClient")

    def __init__(
        self,
        endpoint: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Init."""
        self._request_counter = itertools.count()
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)
        self.health_uri = URI(f"{self.endpoint_uri}/health")
        self.timeout = timeout
        self.extra_headers = extra_headers

    def _build_request_kwargs(self, body: Body, is_async: bool) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.extra_headers:
            headers.update(self.extra_headers)
        data = body.to_json()
        data_kwarg = "content" if is_async else "data"
        return {"url": self.endpoint_uri, "headers": headers, data_kwarg: data}

    def _before_request(self, body: Body, is_async: bool) -> Dict[str, Any]:
        return self._build_request_kwargs(body=body, is_async=is_async)

    def _after_request(self, raw_response: Union[requests.Response, httpx.Response]) -> RPCResponse:
        raw_response.raise_for_status()
        return cast(RPCResponse, self.json_decode(raw_response.text))
