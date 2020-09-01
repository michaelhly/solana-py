"""RPC types."""
from typing import Any, NewType, Union

from typing_extensions import Literal, TypedDict  # noqa: F401

URI = NewType("URI", str)
"""Type for endpoint URI."""

RPCMethod = NewType("RPCMethod", str)
"""Type for RPC method."""


class RPCError(TypedDict):
    """RPC error."""

    code: int
    """HTTP status code."""
    message: str
    """Error message."""


class RPCResponse(TypedDict, total=False):
    """RPC Response."""

    error: Union[RPCError, str]
    """RPC error."""
    id: int
    """Request ID."""
    jsonrpc: Literal["2.0"]
    """Protocol."""
    result: Any
    """Response results."""
