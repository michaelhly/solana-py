"""Pydantic models for the solana package."""

from __future__ import annotations

from solders.pubkey import Pubkey

from solana._pydantic import PydanticModel


class WithdrawFromVoteAccountParams(PydanticModel):
    """Transfer SOL from vote account to identity."""

    vote_account_from_pubkey: Pubkey
    """Vote account to withdraw from."""
    to_pubkey: Pubkey
    """Recipient of the withdrawn SOL."""
    lamports: int
    """Amount of lamports to withdraw."""
    withdrawer: Pubkey
    """Withdrawer authority."""
