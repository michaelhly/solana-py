"""HTTP RPC Provider."""
from typing import Type, overload, Tuple

import requests
from solders.rpc.requests import Body
from solders.rpc.responses import RPCResult

from ...exceptions import SolanaRpcException, handle_exceptions
from .base import BaseProvider
from .core import (
    T,
    _after_request_unparsed,
    _HTTPProviderCore,
    _parse_raw,
    _parse_raw_batch,
    _Tup,
    _Tup1,
    _Tup2,
    _Tup3,
    _Tup4,
    _Tup5,
    _Tuples,
    _RespTup,
    _RespTup1,
    _RespTup2,
    _RespTup3,
    _RespTup4,
    _RespTup5,
    _BodiesTup,
    _BodiesTup1,
    _BodiesTup2,
    _BodiesTup3,
    _BodiesTup4,
    _BodiesTup5,
)


class HTTPProvider(BaseProvider, _HTTPProviderCore):
    """HTTP provider to interact with the http rpc endpoint."""

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"HTTP RPC connection {self.endpoint_uri}"

    @handle_exceptions(SolanaRpcException, requests.exceptions.RequestException)
    def make_request(self, body: Body, parser: Type[T]) -> T:
        """Make an HTTP request to an http rpc endpoint."""
        raw = self.make_request_unparsed(body)
        return _parse_raw(raw, parser=parser)

    def make_request_unparsed(self, body: Body) -> str:
        """Make an async HTTP request to an http rpc endpoint."""
        request_kwargs = self._before_request(body=body, is_async=False)
        raw_response = requests.post(**request_kwargs)
        return _after_request_unparsed(raw_response)

    def make_batch_request_unparsed(self, reqs: Tuple[Body, ...]) -> str:
        """Make an async HTTP request to an http rpc endpoint."""
        request_kwargs = self._before_batch_request(reqs, is_async=False)
        raw_response = requests.post(**request_kwargs)
        return _after_request_unparsed(raw_response)

    @overload
    def make_batch_request(self, reqs: _BodiesTup, parsers: _Tup) -> _RespTup:
        ...

    @overload
    def make_batch_request(self, reqs: _BodiesTup1, parsers: _Tup1) -> _RespTup1:
        ...

    @overload
    def make_batch_request(self, reqs: _BodiesTup2, parsers: _Tup2) -> _RespTup2:
        ...

    @overload
    def make_batch_request(self, reqs: _BodiesTup3, parsers: _Tup3) -> _RespTup3:
        ...

    @overload
    def make_batch_request(self, reqs: _BodiesTup4, parsers: _Tup4) -> _RespTup4:
        ...

    @overload
    def make_batch_request(self, reqs: _BodiesTup5, parsers: _Tup5) -> _RespTup5:
        ...

    def make_batch_request(self, reqs: Tuple[Body, ...], parsers: _Tuples) -> Tuple[RPCResult, ...]:
        """Make a HTTP batch request to an http rpc endpoint.

        Args:
            reqs: A tuple of request objects from ``solders.rpc.requests``.
            parsers: A tuple of response classes from ``solders.rpc.responses``.
                Note: ``parsers`` should line up with ``reqs``.

        Example:
            >>> from solana.rpc.providers.http import HTTPProvider
            >>> from solders.rpc.requests import GetBlockHeight, GetFirstAvailableBlock
            >>> from solders.rpc.responses import GetBlockHeightResp, GetFirstAvailableBlockResp
            >>> provider = HTTPProvider("https://api.devnet.solana.com")
            >>> reqs = (GetBlockHeight(), GetFirstAvailableBlock())
            >>> parsers = (GetBlockHeightResp, GetFirstAvailableBlockResp)
            >>> provider.make_batch_request(reqs, parsers) # doctest: +SKIP
            (GetBlockHeightResp(
                158613909,
            ), GetFirstAvailableBlockResp(
                86753592,
            ))
        """
        raw = self.make_batch_request_unparsed(reqs)
        return _parse_raw_batch(raw, parsers)

    def is_connected(self) -> bool:
        """Health check."""
        try:
            response = requests.get(self.health_uri)
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:
            self.logger.error("Health check failed with error: %s", str(err))
            return False

        return response.ok
