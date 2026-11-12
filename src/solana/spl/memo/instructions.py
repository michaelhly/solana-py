"""Memo program instructions."""

from __future__ import annotations

from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey

from solana._pydantic import PydanticModel
from solana.spl.memo.programs import MEMO_PROGRAM_ID


class AddMemoParams(PydanticModel):
    """Input for `add_memo`."""

    memo: str
    """Memo text, written to the transaction log as UTF-8."""
    signers: tuple[Pubkey, ...] = ()
    """Accounts that must sign the transaction to attest the memo."""
    program_id: Pubkey = MEMO_PROGRAM_ID
    """Memo program to invoke."""


class ParsedAddMemoInstruction(PydanticModel):
    """Result of `parse_add_memo`."""

    program_id: Pubkey
    signers: tuple[Pubkey, ...]
    memo: str


def add_memo(params: AddMemoParams) -> Instruction:
    """Build an instruction that writes a memo to the transaction log.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> signer = Pubkey.from_bytes(bytes([1] * 32))
        >>> ix = add_memo(AddMemoParams(memo="hello", signers=(signer,)))
        >>> ix.data
        b'hello'
        >>> parse_add_memo(ix).signers == (signer,)
        True
    """
    accounts = [AccountMeta(pubkey=s, is_signer=True, is_writable=False) for s in params.signers]
    return Instruction(program_id=params.program_id, data=params.memo.encode("utf-8"), accounts=accounts)


def parse_add_memo(instruction: Instruction) -> ParsedAddMemoInstruction:
    """Decode an add-memo instruction.

    The program id is not checked, so custom deployments can be parsed.

    Raises:
        ValueError: If the data is not valid UTF-8 or an account is not a signer.
    """
    if not all(a.is_signer for a in instruction.accounts):
        raise ValueError("Memo accounts must all be signers.")
    return ParsedAddMemoInstruction(
        program_id=instruction.program_id,
        signers=tuple(a.pubkey for a in instruction.accounts),
        memo=instruction.data.decode("utf-8"),
    )
