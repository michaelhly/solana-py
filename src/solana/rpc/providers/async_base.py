"""Async base RPC Provider."""

from typing import Any, Coroutine, Type

from solders.rpc.requests import Body

from .core import T


class AsyncBaseProvider:
    """Base class for async RPC providers to implement."""

    def make_request(self, body: Body, parser: Type[T]) -> Coroutine[Any, Any, T]:
        """Make a request ot the rpc endpoint."""
        raise NotImplementedError("Providers must implement this method")
