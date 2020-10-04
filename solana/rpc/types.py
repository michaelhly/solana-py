"""RPC types."""
from typing import Any, NamedTuple, NewType, Optional, Union

from typing_extensions import Literal, TypedDict  # noqa: F401

from solana.publickey import PublicKey

from .commitment import Commitment, Max

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


class DataSliceOpts(NamedTuple):
    """Option to limit the returned account data, only available for "base58" or "base64" encoding."""

    offset: int
    """Limit the returned account data using the provided offset: <usize>."""
    length: int
    """Limit the returned account data using the provided length: <usize>."""


class MemcmpOpts(NamedTuple):
    """Option to compare a provided series of bytes with program account data at a particular offset."""

    offset: int
    """Offset into program account data to start comparison: <usize>."""
    bytes: str
    """Data to match, as base-58 encoded string: <string>."""


class TokenAccountOpts(NamedTuple):
    """Options when querying token accounts.

    Provide one of mint or program_id.
    """

    mint: Optional[PublicKey] = None
    """Public key of the specific token Mint to limit accounts to."""
    program_id: Optional[PublicKey] = None
    """Public key of the Token program ID that owns the accounts."""
    encoding: str = "base64"
    """Encoding for Account data, either "base58" (slow), "base64" or jsonParsed".

    Parsed-JSON encoding attempts to use program-specific state parsers to return more
    human-readable and explicit account state data. If parsed-JSON is requested but a
    valid mint cannot be found for a particular account, that account will be filtered out
    from results. jsonParsed encoding is UNSTABLE.
    """
    data_slice: Optional[DataSliceOpts] = None
    """Option to limit the returned account data, only available for "base58" or "base64" encoding."""


class TxOpts(NamedTuple):
    """Options to specify when broadcasting a transaction."""

    skip_confirmation: bool = True
    """If false, `send_transaction` will try to confirm that the transaction was successfully broadcasted.

    When confirming a transaction, `send_transaction` will block for a maximum of 30 seconds. Wrap the call
    inside a thread to make it asynchronous.
    """
    skip_preflight: bool = False
    """If true, skip the preflight transaction checks."""
    preflight_commitment: Commitment = Max
    """Commitment level to use for preflight."""
