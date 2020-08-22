"""Library to interface with system programs."""
from __future__ import annotations
from typing import Any, List, NamedTuple

from solanaweb3.instruction import InstructionLayout, decode_data, encode_data
from solanaweb3.publickey import PublicKey
from solanaweb3.transaction import AccountMeta, Transaction, TransactionInstruction

# Instruction Indices
_CREATE = 0
_ASSIGN = 1
_TRANSFER = 2
_CREATE_WITH_SEED = 3
_ADVANCE_NONCE_ACCOUNT = 4
_WITHDRAW_NONCE_ACCOUNT = 5
_INITIALZE_NONCE_ACCOUNT = 6
_AUTHORIZE_NONCE_ACCOUNT = 7
_ALLOCATE = 8
_ALLOCATE_WITH_SEED = 9
_ASSIGN_WITH_SEED = 10

# Instruction Params
class TransferParams(NamedTuple):
    """Parameters for transfer instruction.

    :param from_pubkey: PublicKey\n
    :param to_pubkey: PublicKey\n
    :lamports: int\n
    """

    from_pubkey: PublicKey
    to_pubkey: PublicKey
    lamports: int


SYSTEM_INSTRUCTION_LAYOUTS: List[InstructionLayout] = [
    InstructionLayout(idx=_CREATE, fmt="<Iqq32s"),
    InstructionLayout(idx=_ASSIGN, fmt="<I32s"),
    InstructionLayout(idx=_TRANSFER, fmt="<Iq"),
    InstructionLayout(idx=_CREATE_WITH_SEED, fmt=""),
    InstructionLayout(idx=_ADVANCE_NONCE_ACCOUNT, fmt="<I"),
    InstructionLayout(idx=_WITHDRAW_NONCE_ACCOUNT, fmt="<Iq"),
    InstructionLayout(idx=_INITIALZE_NONCE_ACCOUNT, fmt="<I32s"),
    InstructionLayout(idx=_AUTHORIZE_NONCE_ACCOUNT, fmt="<I32s"),
    InstructionLayout(idx=_ALLOCATE, fmt="<I32s"),
    InstructionLayout(idx=_ALLOCATE_WITH_SEED, fmt=""),
    InstructionLayout(idx=_ASSIGN_WITH_SEED, fmt=""),
]


class SystemInstruction:
    """System Instruction class to decode transaction instruction data."""

    @staticmethod
    def __check_key_length(keys: List[Any], expected_length: int) -> None:
        if len(keys) < expected_length:
            raise ValueError(f"invalid instruction: found {len(keys)} keys, expected at least {expected_length}")

    @staticmethod
    def __check_program_id(program_id: PublicKey) -> None:
        if program_id != SystemProgram.program_id():
            raise ValueError("invalid instruction: programId is not SystemProgram")

    @staticmethod
    def decode_transfer(instruction: TransactionInstruction) -> TransferParams:
        """Decode a transfer system instruction and retrieve the instruction params."""
        SystemInstruction.__check_program_id(instruction.program_id)
        SystemInstruction.__check_key_length(instruction.keys, 2)

        layout = SYSTEM_INSTRUCTION_LAYOUTS[_TRANSFER]
        data = decode_data(layout, instruction.data)

        return TransferParams(
            from_pubkey=instruction.keys[0].pubkey, to_pubkey=instruction.keys[1].pubkey, lamports=data[1]
        )


class SystemProgram:
    """Factory class for transactions to interact with the System program."""

    @staticmethod
    def program_id() -> PublicKey:
        """Public key that identifies the System program."""
        return PublicKey("11111111111111111111111111111111")

    @staticmethod
    def transfer(params: TransferParams) -> Transaction:
        """Generate a Transaction that transfers lamports from one account to another."""
        layout = SYSTEM_INSTRUCTION_LAYOUTS[_TRANSFER]
        data = encode_data(layout, params.lamports)

        txn = Transaction()
        txn.add(
            TransactionInstruction(
                keys=[
                    AccountMeta(pubkey=params.from_pubkey, is_signer=True, is_writable=True),
                    AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
                ],
                program_id=SystemProgram.program_id(),
                data=data,
            )
        )
        return txn
