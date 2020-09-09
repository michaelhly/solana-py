"""Token instruction layouts."""
from enum import IntEnum

from construct import Int8ul, Int64ul, Pass  # type: ignore
from construct import Struct as cStruct
from construct import Switch

from solana._layouts.shared import PUBLIC_KEY_LAYOUT


class InstructionType(IntEnum):
    """Token instruction types."""

    InitializeMint = 0
    InitializeAccount = 1
    InitializeMultisig = 2
    Transfer = 3
    Approve = 4
    Revoke = 5
    SetAuthority = 6
    MintTo = 7
    Burn = 8
    CloseAccount = 9
    FreezeAccount = 10
    ThawAccount = 11
    Transfer2 = 12
    Approve2 = 13
    MintTo2 = 14
    Burn2 = 15


_INITIALIZE_MINT_LAYOUT = cStruct(
    "decimals" / Int8ul,
    "mint_authority" / PUBLIC_KEY_LAYOUT,
    "freeze_authority_option" / Int8ul,
    "freeze_authority" / PUBLIC_KEY_LAYOUT,
)

_INITIALIZE_MULTISIG_LAYOUT = cStruct("m" / Int8ul)

_AMOUNT_LAYOUT = cStruct("amount" / Int64ul)

_SET_AUTHORITY_LAYOUT = cStruct(
    "authority_type" / Int8ul, "new_authority_option" / Int8ul, "new_authority" / PUBLIC_KEY_LAYOUT
)

_AMOUNT2_LAYOUT = cStruct("amount" / Int64ul, "decimals" / Int8ul)

INSTRUCTIONS_LAYOUT = cStruct(
    "instruction_type" / Int8ul,
    "args"
    / Switch(
        lambda this: this.instruction_type,
        {
            InstructionType.InitializeMint: _INITIALIZE_MINT_LAYOUT,
            InstructionType.InitializeAccount: Pass,
            InstructionType.InitializeMultisig: _INITIALIZE_MULTISIG_LAYOUT,
            InstructionType.Transfer: _AMOUNT_LAYOUT,
            InstructionType.Approve: _AMOUNT_LAYOUT,
            InstructionType.Revoke: Pass,
            InstructionType.SetAuthority: _SET_AUTHORITY_LAYOUT,
            InstructionType.MintTo: _AMOUNT_LAYOUT,
            InstructionType.Burn: _AMOUNT_LAYOUT,
            InstructionType.CloseAccount: Pass,
            InstructionType.FreezeAccount: Pass,
            InstructionType.ThawAccount: Pass,
            InstructionType.Transfer2: _AMOUNT2_LAYOUT,
            InstructionType.Approve2: _AMOUNT2_LAYOUT,
            InstructionType.MintTo2: _AMOUNT2_LAYOUT,
            InstructionType.Burn2: _AMOUNT2_LAYOUT,
        },
    ),
)
