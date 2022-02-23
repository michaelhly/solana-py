"""Library to interface with the vote program."""
from __future__ import annotations

from typing import NamedTuple

from solana._layouts.vote_instructions import VOTE_INSTRUCTIONS_LAYOUT, InstructionType
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction

VOTE_PROGRAM_ID: PublicKey = PublicKey("Vote111111111111111111111111111111111111111")
"""Public key that identifies the Vote program."""


# Instrection Params
class WithdrawFromVoteAccountParams(NamedTuple):
    """Transfer SOL from vote account to identity."""

    vote_account_from_pubkey: PublicKey
    """"""
    to_pubkey: PublicKey
    """"""
    lamports: int
    """"""
    withdrawer: PublicKey
    """"""


def withdraw_from_vote_account(params: WithdrawFromVoteAccountParams) -> TransactionInstruction:
    """Generate an instruction that transfers lamports from a vote account to any other.

    Example:

        >>> from solana.publickey import PublicKey
        >>> from solana.keypair import Keypair
        >>> vote = PublicKey(1)
        >>> withdrawer = Keypair.from_seed(bytes([0]*32))
        >>> instruction = withdraw_from_vote_account(
        ...    WithdrawFromVoteAccountParams(
        ...        vote_account_from_pubkey=vote,
        ...        to_pubkey=withdrawer,
        ...        withdrawer=withdrawer,
        ...        lamports=3_000_000_000,
        ...    )
        ... )
        >>> type(instruction)
        <class 'solana.transaction.TransactionInstruction'>

    Returns:
        The generated instruction.
    """
    data = VOTE_INSTRUCTIONS_LAYOUT.build(
        dict(instruction_type=InstructionType.WITHDRAW_FROM_VOTE_ACCOUNT, args=dict(lamports=params.lamports))
    )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.vote_account_from_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.withdrawer, is_signer=True, is_writable=True),
        ],
        program_id=VOTE_PROGRAM_ID,
        data=data,
    )
