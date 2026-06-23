"""Pydantic models for memo program instructions."""

from __future__ import annotations

from solders.pubkey import Pubkey

from solana._pydantic import PydanticModel


class MemoParams(PydanticModel):
    """Create memo transaction params."""

    program_id: Pubkey
    """Memo program account."""
    signer: Pubkey
    """Signing account."""
    message: bytes
    """Memo message in bytes."""
