"""Helper code for HTTP provider classes."""
import itertools
import logging
import os
from typing import Any, Dict, Optional, Type, TypeVar, Union, Tuple, overload

import httpx
import requests
from solders.rpc.requests import Body, batch_to_json as batch_req_json
from solders.rpc.responses import (
    Resp,
    RPCError,
    batch_from_json as batch_resp_json,
    RPCResult,
)

from ..core import RPCException
from ..types import URI

DEFAULT_TIMEOUT = 10


T = TypeVar("T", bound=RPCResult)
# hacky solution for parsing batches of up to six
_T1 = TypeVar("_T1", bound=RPCResult)
_T2 = TypeVar("_T2", bound=RPCResult)
_T3 = TypeVar("_T3", bound=RPCResult)
_T4 = TypeVar("_T4", bound=RPCResult)
_T5 = TypeVar("_T5", bound=RPCResult)

_Tup = Tuple[Type[T]]
_Tup1 = Tuple[Type[T], Type[_T1]]
_Tup2 = Tuple[Type[T], Type[_T1], Type[_T2]]
_Tup3 = Tuple[Type[T], Type[_T1], Type[_T2], Type[_T3]]
_Tup4 = Tuple[Type[T], Type[_T1], Type[_T2], Type[_T3], Type[_T4]]
_Tup5 = Tuple[Type[T], Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]]
_Tuples = Union[_Tup, _Tup1, _Tup2, _Tup3, _Tup4, _Tup5]

_RespTup = Tuple[Resp[T]]
_RespTup1 = Tuple[Resp[T], Resp[_T1]]
_RespTup2 = Tuple[Resp[T], Resp[_T1], Resp[_T2]]
_RespTup3 = Tuple[Resp[T], Resp[_T1], Resp[_T2], Resp[_T3]]
_RespTup4 = Tuple[Resp[T], Resp[_T1], Resp[_T2], Resp[_T3], Resp[_T4]]
_RespTup5 = Tuple[Resp[T], Resp[_T1], Resp[_T2], Resp[_T3], Resp[_T4], Resp[_T5]]

_BodiesTup = Tuple[Body]
_BodiesTup1 = Tuple[Body, Body]
_BodiesTup2 = Tuple[Body, Body, Body]
_BodiesTup3 = Tuple[Body, Body, Body, Body]
_BodiesTup4 = Tuple[Body, Body, Body, Body, Body]
_BodiesTup5 = Tuple[Body, Body, Body, Body, Body, Body]


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANARPC_HTTP_URI", "http://localhost:8899"))


class _HTTPProviderCore:  # pylint: disable=too-few-public-methods
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

    def _build_common_request_kwargs(self, is_async: bool) -> Tuple[Dict[str, Any], str]:
        headers = {"Content-Type": "application/json"}
        if self.extra_headers:
            headers.update(self.extra_headers)
        data_kwarg = "content" if is_async else "data"
        return {"url": self.endpoint_uri, "headers": headers}, data_kwarg

    def _build_request_kwargs(self, body: Body, is_async: bool) -> Dict[str, Any]:
        common_kwargs, data_kwarg = self._build_common_request_kwargs(is_async)
        data = body.to_json()
        return {**common_kwargs, data_kwarg: data}

    def _build_batch_request_kwargs(self, reqs: Tuple[Body, ...], is_async: bool) -> Dict[str, Any]:
        common_kwargs, data_kwarg = self._build_common_request_kwargs(is_async)
        data = batch_req_json(reqs)
        return {**common_kwargs, data_kwarg: data}

    def _before_request(self, body: Body, is_async: bool) -> Dict[str, Any]:
        return self._build_request_kwargs(body=body, is_async=is_async)

    def _before_batch_request(self, reqs: Tuple[Body, ...], is_async: bool) -> Dict[str, Any]:
        return self._build_batch_request_kwargs(reqs, is_async=is_async)


def _parse_raw(raw: str, parser: Type[T]) -> T:
    parsed = parser.from_json(raw)  # type: ignore
    if isinstance(parsed, RPCError.__args__):  # type: ignore # TODO: drop py37 and use typing.get_args
        raise RPCException(parsed)
    return parsed


@overload
def _parse_raw_batch(raw: str, parsers: _Tup) -> _RespTup:
    ...


@overload
def _parse_raw_batch(raw: str, parsers: _Tup1) -> _RespTup1:
    ...


@overload
def _parse_raw_batch(raw: str, parsers: _Tup2) -> _RespTup2:
    ...


@overload
def _parse_raw_batch(raw: str, parsers: _Tup3) -> _RespTup3:
    ...


@overload
def _parse_raw_batch(raw: str, parsers: _Tup4) -> _RespTup4:
    ...


@overload
def _parse_raw_batch(raw: str, parsers: _Tup5) -> _RespTup5:
    ...


def _parse_raw_batch(raw: str, parsers: _Tuples) -> Tuple[RPCResult, ...]:
    return tuple(batch_resp_json(raw, parsers))


def _after_request_unparsed(raw_response: Union[requests.Response, httpx.Response]) -> str:
    raw_response.raise_for_status()
    return raw_response.text


@overload
def _after_batch_request(raw_response: Union[requests.Response, httpx.Response], parsers: _Tup) -> _RespTup:
    ...


@overload
def _after_batch_request(raw_response: Union[requests.Response, httpx.Response], parsers: _Tup1) -> _RespTup1:
    ...


@overload
def _after_batch_request(raw_response: Union[requests.Response, httpx.Response], parsers: _Tup2) -> _RespTup2:
    ...


@overload
def _after_batch_request(raw_response: Union[requests.Response, httpx.Response], parsers: _Tup3) -> _RespTup3:
    ...


@overload
def _after_batch_request(raw_response: Union[requests.Response, httpx.Response], parsers: _Tup4) -> _RespTup4:
    ...


@overload
def _after_batch_request(raw_response: Union[requests.Response, httpx.Response], parsers: _Tup5) -> _RespTup5:
    ...


def _after_batch_request(
    raw_response: Union[requests.Response, httpx.Response], parsers: _Tuples
) -> Tuple[RPCResult, ...]:
    text = _after_request_unparsed(raw_response)
    return _parse_raw_batch(text, parsers)  # type: ignore
