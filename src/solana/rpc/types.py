"""RPC types."""

from __future__ import annotations

from typing import NewType

from typing_extensions import TypedDict


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
