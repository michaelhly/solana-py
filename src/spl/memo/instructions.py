"""Memo program instructions."""
from __future__ import annotations

from typing import NamedTuple

from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction


class MemoParams(NamedTuple):
    """Create memo transaction params."""

    program_id: PublicKey
    """Memo program account."""
    signer: PublicKey
    """Signing account."""
    message: bytes
    """Memo message in bytes."""


def decode_create_memo(instruction: TransactionInstruction) -> MemoParams:
    """Decode a create_memo_instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    return MemoParams(signer=instruction.keys[0].pubkey, message=instruction.data, program_id=instruction.program_id)


def create_memo(params: MemoParams) -> TransactionInstruction:
    """Creates a transaction instruction that creates a memo.

    Message need to be encoded in bytes.

    Example:

        >>> signer, memo_program = PublicKey(1), PublicKey(2)
        >>> message = bytes("test", encoding="utf8")
        >>> params = MemoParams(
        ...     program_id=memo_program,
        ...     message=message,
        ...     signer=signer
        ... )
        >>> type(create_memo(params))
        <class 'solana.transaction.TransactionInstruction'>

    Returns:
        The instruction to create a memo.
    """
    keys = [
        AccountMeta(pubkey=params.signer, is_signer=True, is_writable=True),
    ]
    return TransactionInstruction(
        keys=keys,
        program_id=params.program_id,
        data=params.message,
    )
