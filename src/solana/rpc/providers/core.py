"""Helper code for HTTP provider classes."""
import itertools
import logging
import os
from typing import Any, Dict, Optional, Union, TypeVar, Type
from solders.rpc.requests import Body
from solders.rpc.responses import RPCResult as RPCResultType, RpcError

import httpx
import requests

from .._utils.encoding import FriendlyJsonSerde
from ..types import URI
from ..core import RPCException

DEFAULT_TIMEOUT = 10

T = TypeVar("T", bound=RPCResultType)


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


def _after_request(raw_response: Union[requests.Response, httpx.Response], parser: Type[T]) -> T:
    text = _after_request_raw(raw_response)
    parsed = parser.from_json(text)
    if isinstance(parsed, RpcError):
        raise RPCException(parsed)
    return parsed


def _after_request_raw(raw_response: Union[requests.Response, httpx.Response]) -> str:
    raw_response.raise_for_status()
    return raw_response.text
