"""Base RPC Provider."""
from solders.rpc.requests import Body

from ..types import RPCResponse


class BaseProvider:
    """Base class for RPC providers to implement."""

    def make_request(self, body: Body) -> RPCResponse:
        """Make a request ot the rpc endpoint."""
        raise NotImplementedError("Providers must implement this method")

    def is_connected(self) -> bool:
        """Health check."""
        raise NotImplementedError("Providers must implement this method")
