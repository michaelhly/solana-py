"""RPC types."""
from typing import Any, NewType, Union

from typing_extensions import Literal, TypedDict  # noqa: F401

URI = NewType("URI", str)
RPCMethod = NewType("RPCMethod", str)


class RPCError(TypedDict):
    """RPC error."""

    code: int
    message: str


class RPCResponse(TypedDict, total=False):
    """RPC Response."""

    error: Union[RPCError, str]
    id: int
    jsonrpc: Literal["2.0"]
    result: Any
