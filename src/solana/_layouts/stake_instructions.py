from enum import IntEnum

from construct import (  # type: ignore
    Int32ul,
    Int64sl,
    Int64ul,
    Pass,
    Switch,  # type: ignore
)
from construct import Struct as cStruct
from spl.token._layouts import PUBLIC_KEY_LAYOUT


class StakeInstructionType(IntEnum):
    """Instruction types for staking program."""

    INITIALIZE_STAKE_ACCOUNT = 0
    DELEGATE_STAKE_ACCOUNT = 2
    DEACTIVATE_STAKE_ACCOUNT = 5
    WITHDRAW_STAKE_ACCOUNT = 4


_AUTHORIZED_LAYOUT = cStruct(
    "staker" / PUBLIC_KEY_LAYOUT,
    "withdrawer" / PUBLIC_KEY_LAYOUT,
)

_LOCKUP_LAYOUT = cStruct(
    "unix_timestamp" / Int64sl,
    "epoch" / Int64ul,
    "custodian" / PUBLIC_KEY_LAYOUT,
)

INITIALIZE_STAKE_ACCOUNT_LAYOUT = cStruct(
    "authorized" / _AUTHORIZED_LAYOUT,
    "lockup" / _LOCKUP_LAYOUT,
)

WITHDRAW_STAKE_ACCOUNT_LAYOUT = cStruct(
    "lamports" / Int64ul,
)

DELEGATE_STAKE_INSTRUCTIONS_LAYOUT = cStruct(
    "instruction_type" / Int32ul,
)

STAKE_INSTRUCTIONS_LAYOUT = cStruct(
    "instruction_type" / Int32ul,
    "args"
    / Switch(
        lambda this: this.instruction_type,
        {
            StakeInstructionType.INITIALIZE_STAKE_ACCOUNT: INITIALIZE_STAKE_ACCOUNT_LAYOUT,
            StakeInstructionType.DELEGATE_STAKE_ACCOUNT: cStruct(),
            StakeInstructionType.DEACTIVATE_STAKE_ACCOUNT: Pass,
            StakeInstructionType.WITHDRAW_STAKE_ACCOUNT: WITHDRAW_STAKE_ACCOUNT_LAYOUT,
        },
    ),
)
