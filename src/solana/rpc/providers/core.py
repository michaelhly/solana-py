"""Helper code for HTTP provider classes."""
import itertools
import logging
import os
from typing import Any, Dict, Optional, Tuple, Union, cast

import httpx
import requests

from .._utils.encoding import FriendlyJsonSerde
from ..types import URI, RPCMethod, RPCResponse
from ...utils.helpers import merge_keep_latter

DEFAULT_TIMEOUT = 10


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANARPC_HTTP_URI", "http://localhost:8899"))


class _HTTPProviderCore(FriendlyJsonSerde):
    logger = logging.getLogger("solanaweb3.rpc.httprpc.HTTPClient")

    def __init__(self, endpoint: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        """Init."""
        self._request_counter = itertools.count()
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)
        self.health_uri = URI(f"{self.endpoint_uri}/health")
        self.timeout = timeout

    def _build_request_kwargs(
        self, request_id: int, method: RPCMethod, params: Tuple[Any, ...], is_async: bool
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        data = self.json_encode({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        data_kwarg = "content" if is_async else "data"
        return {"url": self.endpoint_uri, "headers": headers, data_kwarg: data}

    def _increment_counter_and_get_id(self) -> int:
        return next(self._request_counter) + 1

    def _before_request(self, method: RPCMethod, params: Tuple[Any, ...], is_async: bool, **kwargs) -> Dict[str, Any]:
        request_id = self._increment_counter_and_get_id()
        self.logger.debug(
            "Making HTTP request. URI: %s, RequestID: %d, Method: %s, Params: %s",
            self.endpoint_uri,
            request_id,
            method,
            params,
        )
        built_kwargs = self._build_request_kwargs(
            request_id=request_id, method=method, params=params, is_async=is_async
        )
        return merge_keep_latter(built_kwargs, kwargs)

    def _after_request(self, raw_response: Union[requests.Response, httpx.Response], method: RPCMethod) -> RPCResponse:
        raw_response.raise_for_status()
        self.logger.debug(
            "Getting response HTTP. URI: %s, " "Method: %s, Response: %s", self.endpoint_uri, method, raw_response.text
        )
        return cast(RPCResponse, self.json_decode(raw_response.text))
