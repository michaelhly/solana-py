"""Helper code for HTTP provider classes."""

from __future__ import annotations

import itertools
import logging
import os
from typing import Any, Dict, Optional, Type, TypeVar

import httpx2
from solders.rpc.requests import Body
from solders.rpc.responses import RPCError, RPCResult

from ..core import RPCException
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


class _HTTPProviderCore:  # pylint: disable=too-few-public-methods
    logger = logging.getLogger("solana.rpc.providers")

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

    def _build_common_request_kwargs(self) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.extra_headers:
            headers.update(self.extra_headers)
        return {"url": self.endpoint_uri, "headers": headers}

    def _build_request_kwargs(self, body: Body) -> Dict[str, Any]:
        common_kwargs = self._build_common_request_kwargs()
        data = body.to_json()
        return {**common_kwargs, "content": data}

    def _before_request(self, body: Body) -> Dict[str, Any]:
        return self._build_request_kwargs(body=body)


def _parse_raw(raw: str, parser: Type[T]) -> T:
    parsed = parser.from_json(raw)  # type: ignore
    if isinstance(parsed, RPCError.__args__):  # type: ignore # TODO: drop py37 and use typing.get_args
        raise RPCException(parsed)
    return parsed  # type: ignore


def _after_request_unparsed(raw_response: httpx2.Response) -> str:
    raw_response.raise_for_status()
    return raw_response.text
