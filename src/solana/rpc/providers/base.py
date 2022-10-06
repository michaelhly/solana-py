"""Base RPC Provider."""
from typing_extensions import Protocol
from solders.rpc.requests import Body
from solders.rpc.responses import RpcError
from .core import T


class BaseProvider:
    """Base class for RPC providers to implement."""

    def make_request_raw(self, body: Body) -> str:
        """Make a request to the rpc endpoint, without parsing the result."""
        raise NotImplementedError("Providers must implement this method")

    def make_request(self, body: Body, parser: Parser) -> T:
        """Make a request to the rpc endpoint."""
        raise NotImplementedError("Providers must implement this method")

    def is_connected(self) -> bool:
        """Health check."""
        raise NotImplementedError("Providers must implement this method")
