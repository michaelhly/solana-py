"""Byte layouts for system program instructions."""
from enum import IntEnum

from construct import Int32ul, Int64ul, Pass  # type: ignore
from construct import Struct as cStruct
from construct import Switch

from .shared import PUBLIC_KEY_LAYOUT, RUST_STRING_LAYOUT


class InstructionType(IntEnum):
    """Instruction types for system program."""

    CreateAccount = 0
    Assign = 1
    Transfer = 2
    CreateAccountWithSeed = 3
    AdvanceNonceAccount = 4
    WithdrawNonceAccount = 5
    InitializeNonceAccount = 6
    AuthorizeNonceAccount = 7
    Allocate = 8
    AllocateWithSeed = 9
    AssignWithSeed = 10
    TransferWithSeed = 11


_CREATE_ACCOUNT_LAYOUT = cStruct(
    "lamports" / Int64ul,
    "space" / Int64ul,
    "program_id" / PUBLIC_KEY_LAYOUT,
)

_ASSIGN_LAYOUT = cStruct("program_id" / PUBLIC_KEY_LAYOUT)

_TRANFER_LAYOUT = cStruct("lamports" / Int64ul)

_CREATE_ACCOUNT_WTIH_SEED_LAYOUT = cStruct(
    "base" / PUBLIC_KEY_LAYOUT,
    "seed" / RUST_STRING_LAYOUT,
    "lamports" / Int64ul,
    "space" / Int64ul,
    "program_id" / PUBLIC_KEY_LAYOUT,
)

_WITHDRAW_NONCE_ACCOUNT_LAYOUT = cStruct("lamports" / Int64ul)

_INITIALIZE_NONCE_ACCOUNT_LAYOUT = cStruct("authorized" / PUBLIC_KEY_LAYOUT)

_AUTHORIZE_NONCE_ACCOUNT_LAYOUT = cStruct("authorized" / PUBLIC_KEY_LAYOUT)

_ALLOCATE_LAYOUT = cStruct("space" / Int64ul)

_ALLOCATE_WITH_SEED_LAYOUT = cStruct(
    "base" / PUBLIC_KEY_LAYOUT, "seed" / RUST_STRING_LAYOUT, "space" / Int64ul, "program_id" / PUBLIC_KEY_LAYOUT
)

_ASSIGN_WITH_SEED_LAYOUT = cStruct(
    "base" / PUBLIC_KEY_LAYOUT, "seed" / RUST_STRING_LAYOUT, "program_id" / PUBLIC_KEY_LAYOUT
)

_TRANSFER_WITH_SEED_LAYOUT = cStruct(
    "lamports" / Int64ul,
    "from_seed" / RUST_STRING_LAYOUT,
    "from_ower" / PUBLIC_KEY_LAYOUT,
)

SYSTEM_INSTRUCTIONS_LAYOUT = cStruct(
    "instruction_type" / Int32ul,
    "args"
    / Switch(
        lambda this: this.instruction_type,
        {
            InstructionType.CreateAccount: _CREATE_ACCOUNT_LAYOUT,
            InstructionType.Assign: _ASSIGN_LAYOUT,
            InstructionType.Transfer: _TRANFER_LAYOUT,
            InstructionType.CreateAccountWithSeed: _CREATE_ACCOUNT_WTIH_SEED_LAYOUT,
            InstructionType.AdvanceNonceAccount: Pass,  # No args
            InstructionType.WithdrawNonceAccount: _WITHDRAW_NONCE_ACCOUNT_LAYOUT,
            InstructionType.InitializeNonceAccount: _INITIALIZE_NONCE_ACCOUNT_LAYOUT,
            InstructionType.AuthorizeNonceAccount: _AUTHORIZE_NONCE_ACCOUNT_LAYOUT,
            InstructionType.Allocate: _ALLOCATE_LAYOUT,
            InstructionType.AllocateWithSeed: _ALLOCATE_WITH_SEED_LAYOUT,
            InstructionType.AssignWithSeed: _ASSIGN_WITH_SEED_LAYOUT,
            InstructionType.TransferWithSeed: _TRANSFER_WITH_SEED_LAYOUT,
        },
    ),
)
