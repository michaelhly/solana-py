"""Async base RPC Provider."""
from typing import Any

from ..types import RPCMethod, RPCResponse


class AsyncBaseProvider:
    """Base class for async RPC providers to implement."""

    async def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make a request ot the rpc endpoint."""
        raise NotImplementedError("Providers must implement this method")

    async def is_connected(self) -> bool:
        """Health check."""
        raise NotImplementedError("Providers must implement this method")
