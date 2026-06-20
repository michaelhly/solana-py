"""Pydantic models for the solana package.

These are the Pydantic successors to the deprecated ``NamedTuple`` types defined directly
under the :mod:`solana` package (currently the vote program params in
:mod:`solana.vote_program`).
"""

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
