"""Token instruction layouts."""
from enum import IntEnum

from construct import Bytes, Int8ul, Int32ul, Int64ul, Switch
from construct import Struct as cStruct

PUBLIC_KEY_LAYOUT = Bytes(32)


class InstructionType(IntEnum):
    """Token instruction types."""

    REQUEST_UNITS = 0
    REQUEST_HEAP_FRAME = 1
    SET_COMPUTE_UNIT_LIMIT = 2
    SET_COMPUTE_UNIT_PRICE = 3


_REQUEST_UNITS_LAYOUT = cStruct(
    "units" / Int32ul,
    "additional_fee" / Int32ul,
)

_REQUEST_HEAP_FRAME_LAYOUT = cStruct("bytes" / Int32ul)

_SET_COMPUTE_UNIT_LIMIT_LAYOUT = cStruct("units" / Int32ul)

_SET_COMPUTE_UNIT_PRICE_LAYOUT = cStruct("micro_lamports" / Int64ul)

INSTRUCTIONS_LAYOUT = cStruct(
    "instruction_type" / Int8ul,
    "args"
    / Switch(
        lambda this: this.instruction_type,
        {
            InstructionType.REQUEST_UNITS: _REQUEST_UNITS_LAYOUT,
            InstructionType.REQUEST_HEAP_FRAME: _REQUEST_HEAP_FRAME_LAYOUT,
            InstructionType.SET_COMPUTE_UNIT_LIMIT: _SET_COMPUTE_UNIT_LIMIT_LAYOUT,
            InstructionType.SET_COMPUTE_UNIT_PRICE: _SET_COMPUTE_UNIT_PRICE_LAYOUT,
        },
    ),
)
