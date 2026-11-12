"""Memo program instructions."""

from __future__ import annotations

from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey

from solana._pydantic import PydanticModel
from solana.spl.memo.programs import MEMO_V4_PROGRAM_ID


class AddMemoParams(PydanticModel):
    """Input for `add_memo`."""

    memo: str
    """Memo text, written to the transaction log as UTF-8."""
    signers: tuple[Pubkey, ...] = ()
    """Accounts that must sign the transaction to attest the memo."""
    program_id: Pubkey = MEMO_V4_PROGRAM_ID
    """Memo program to invoke."""


class AddMemoInstructionData(PydanticModel):
    """Decoded data of an add-memo instruction."""

    memo: str
    """Memo text."""


class ParsedAddMemoInstruction(PydanticModel):
    """Result of `parse_add_memo`."""

    program_id: Pubkey
    data: AddMemoInstructionData


def add_memo(params: AddMemoParams) -> Instruction:
    """Build an instruction that writes a memo to the transaction log.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> signer = Pubkey.from_bytes(bytes([1] * 32))
        >>> ix = add_memo(AddMemoParams(memo="hello", signers=(signer,)))
        >>> ix.data
        b'hello'
        >>> parse_add_memo(ix).data.memo
        'hello'
    """
    accounts = [AccountMeta(pubkey=s, is_signer=True, is_writable=False) for s in params.signers]
    return Instruction(program_id=params.program_id, data=params.memo.encode("utf-8"), accounts=accounts)


def parse_add_memo(instruction: Instruction) -> ParsedAddMemoInstruction:
    """Decode an add-memo instruction.

    The program id is not checked, so custom deployments can be parsed. Accounts are not
    returned, as the memo program only takes signers.

    Raises:
        ValueError: If the data is not valid UTF-8.
    """
    return ParsedAddMemoInstruction(
        program_id=instruction.program_id,
        data=AddMemoInstructionData(memo=instruction.data.decode("utf-8")),
    )
