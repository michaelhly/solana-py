"""Async base RPC Provider."""

from collections.abc import Coroutine
from typing import Any

from solders.rpc.requests import Body

from .core import T


class AsyncBaseProvider:
    """Base class for async RPC providers to implement."""

    def make_request(self, body: Body, parser: type[T]) -> Coroutine[Any, Any, T]:
        """Make a request to the rpc endpoint."""
        raise NotImplementedError("Providers must implement this method")
