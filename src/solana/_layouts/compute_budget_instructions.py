"""Byte layouts for vote program instructions."""
from enum import IntEnum

from construct import (
    Int32ul,
    Int64ul,
    Switch,  # type: ignore
)
from construct import Struct as cStruct


class InstructionType(IntEnum):
    """Instruction types for vote program."""

    REQUEST_UNITS_DEPRECATED = 0
    REQUEST_HEAP_FRAME = 1
    SET_COMPUTE_UNIT_LIMIT = 2
    SET_COMPUTE_UNIT_PRICE = 3
    SET_LOADED_ACCOUNTS_DATA_SIZE_LIMIT = 4


REQUEST_UNITS_DEPRECATED_LAYOUT = cStruct("units" / Int32ul, "additional_fee" / Int32ul)
REQUEST_HEAP_FRAME_LAYOUT = cStruct("value" / Int32ul)
SET_COMPUTE_UNIT_LIMIT_LAYOUT = cStruct("value" / Int32ul)
SET_COMPUTE_UNIT_PRICE_LAYOUT = cStruct("value" / Int64ul)
SET_LOADED_ACCOUNTS_DATA_SIZE_LIMIT_LAYOUT = cStruct("value" / Int32ul)

COMPUTE_BUDGET_INSTRUCTIONS_LAYOUT = cStruct(
    "instruction_type" / Int32ul,
    "args"
    / Switch(
        lambda this: this.instruction_type,
        {
            InstructionType.REQUEST_UNITS_DEPRECATED: REQUEST_UNITS_DEPRECATED_LAYOUT,
            InstructionType.REQUEST_HEAP_FRAME: REQUEST_HEAP_FRAME_LAYOUT,
            InstructionType.SET_COMPUTE_UNIT_LIMIT: SET_COMPUTE_UNIT_LIMIT_LAYOUT,
            InstructionType.SET_COMPUTE_UNIT_PRICE: SET_COMPUTE_UNIT_PRICE_LAYOUT,
            InstructionType.SET_LOADED_ACCOUNTS_DATA_SIZE_LIMIT: SET_LOADED_ACCOUNTS_DATA_SIZE_LIMIT_LAYOUT,
        },
    ),
)
