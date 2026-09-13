"""Pydantic models for RPC types."""

from __future__ import annotations

from solders.pubkey import Pubkey

from solana._pydantic import PydanticModel

from .commitment import Commitment, Finalized


class DataSliceOpts(PydanticModel):
    """Option to limit the returned account data, only available for "base58" or "base64" encoding."""

    offset: int
    """Limit the returned account data using the provided offset: <usize>."""
    length: int
    """Limit the returned account data using the provided length: <usize>."""


class MemcmpOpts(PydanticModel):
    """Option to compare a provided series of bytes with program account data at a particular offset."""

    offset: int
    """Offset into program account data to start comparison: <usize>."""
    bytes: str
    """Data to match, as base-58 encoded string: <string>."""


class TokenAccountOpts(PydanticModel):
    """Options when querying token accounts.

    Provide one of mint or program_id.
    """

    mint: Pubkey | None = None
    """Public key of the specific token Mint to limit accounts to."""
    program_id: Pubkey | None = None
    """Public key of the Token program ID that owns the accounts."""
    encoding: str = "base64"
    """Encoding for Account data, either "base58" (slow), "base64", or "jsonParsed"."""
    data_slice: DataSliceOpts | None = None
    """Option to limit the returned account data, only available for "base58" or "base64" encoding."""


class ClusterUrls(PydanticModel):
    """A collection of urls for each cluster."""

    devnet: str
    testnet: str
    mainnet_beta: str


class Endpoint(PydanticModel):
    """Container for http and https cluster urls."""

    http: ClusterUrls
    https: ClusterUrls


class TxOpts(PydanticModel):
    """Options to specify when broadcasting a transaction."""

    skip_confirmation: bool = True
    """If false, `send_transaction` will await confirmation that the transaction was successfully broadcasted.

    When confirming a transaction, `send_transaction` polls for the transaction status until it is confirmed,
    the blockhash expires (when `last_valid_block_height` is set), or a 90-second timeout elapses. The call is
    asynchronous, so other tasks can continue to run while awaiting confirmation.
    """
    skip_preflight: bool = False
    """If true, skip the preflight transaction checks."""
    preflight_commitment: Commitment = Finalized
    """Commitment level to use for preflight."""
    max_retries: int | None = None
    """Maximum number of times for the RPC node to retry sending the transaction to the leader.
    If this parameter not provided, the RPC node will retry the transaction until it is finalized
    or until the blockhash expires.
    """
    last_valid_block_height: int | None = None
    """Pass the latest valid block height here, to be consumed by confirm_transaction.
    Valid only if skip_confirmation is False.
    """
