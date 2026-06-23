"""Pydantic models for the solana package."""

from __future__ import annotations

from solders.pubkey import Pubkey

from solana._pydantic import PydanticModel


class WithdrawFromVoteAccountParams(PydanticModel):
    """Transfer SOL from vote account to identity."""

    vote_account_from_pubkey: Pubkey
    """"""
    to_pubkey: Pubkey
    """"""
    lamports: int
    """"""
    withdrawer: Pubkey
    """"""
