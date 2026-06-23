"""Memo program instructions."""

from __future__ import annotations

from solders.instruction import AccountMeta, Instruction

from spl.memo import models


def decode_create_memo(instruction: Instruction) -> models.MemoParams:
    """Decode a create_memo_instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    return models.MemoParams(
        signer=instruction.accounts[0].pubkey,
        message=instruction.data,
        program_id=instruction.program_id,
    )


def create_memo(params: models.MemoParams) -> Instruction:
    """Creates a transaction instruction that creates a memo.

    Message need to be encoded in bytes.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> from spl.memo.models import MemoParams
        >>> leading_zeros = [0] * 31
        >>> signer, memo_program = Pubkey(leading_zeros + [1]), Pubkey(leading_zeros + [2])
        >>> message = bytes("test", encoding="utf8")
        >>> params = MemoParams(
        ...     program_id=memo_program,
        ...     message=message,
        ...     signer=signer
        ... )
        >>> type(create_memo(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to create a memo.
    """
    keys = [
        AccountMeta(pubkey=params.signer, is_signer=True, is_writable=True),
    ]
    return Instruction(
        accounts=keys,
        program_id=params.program_id,
        data=params.message,
    )
