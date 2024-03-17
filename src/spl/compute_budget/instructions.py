"""Instructions for the Compute Budget program."""
from typing import NamedTuple, Any

from solders.instruction import Instruction
from typing_extensions import deprecated

from solana.utils.validate import validate_instruction_keys, validate_instruction_type
from spl.compute_budget.constants import COMPUTE_BUDGET_PROGRAM_ID
from spl.compute_budget._layouts import (
    InstructionType,
    INSTRUCTIONS_LAYOUT,
)

"""

class InstructionType(IntEnum):
    REQUEST_UNITS = 0
    REQUEST_HEAP_FRAME = 1
    SET_COMPUTE_UNIT_LIMIT = 2
    SET_COMPUTE_UNIT_PRICE = 3

_REQUEST_UNITS_LAYOUT = cStruct(
    "instruction" / Int8ul,
    "units" / Int32ul,
    "additional_fee" / Int32ul,
)

_REQUEST_HEAP_FRAME_LAYOUT = cStruct("instruction" / Int8ul, "bytes" / Int32ul)

_SET_COMPUTE_UNIT_LIMIT_LAYOUT = cStruct("instruction" / Int8ul, "units" / Int32ul)

_SET_COMPUTE_UNIT_PRICE_LAYOUT = cStruct("instruction" / Int8ul, "micro_lamports" / Int64ul)

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

"""


@deprecated("Use SetComputeUnitLimitParams instead.")
class RequestUnitsParams(NamedTuple):
    """Request units transaction params."""

    units: int
    """Units."""
    additional_fee: int
    """Additional fee."""


class RequestHeapFrameParams(NamedTuple):
    """Request heap frame transaction params."""

    bytes: int  # noqa: A003
    """The amount of heap frame bytes to additionally request. 32K = 8 Compute Units."""


class SetComputeUnitLimitParams(NamedTuple):
    """Set compute unit limit transaction params."""

    units: int
    """Maximum compute units."""


class SetComputeUnitPriceParams(NamedTuple):
    """Set compute unit price transaction params."""

    micro_lamports: int
    """Priority fee of one compute unit in micro Lamports. 1 micro Lamport = 0.000001 Lamport = 10^-15 SOL."""


def __parse_and_validate_instruction(
    instruction: Instruction,
    expected_keys: int,
    expected_type: InstructionType,
) -> Any:  # Returns a Construct container.
    validate_instruction_keys(instruction, expected_keys)
    data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(data, expected_type)
    return data


@deprecated("Use SetComputeUnitLimit instruction instead.")
def decode_request_units(instruction: Instruction) -> RequestUnitsParams:
    """Decode a request_units instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 0, InstructionType.REQUEST_UNITS)
    return RequestUnitsParams(
        units=parsed_data.args.units,
        additional_fee=parsed_data.args.additional_fee,
    )


def decode_request_heap_frame(instruction: Instruction) -> RequestHeapFrameParams:
    """Decode a request_heap_frame instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 0, InstructionType.REQUEST_HEAP_FRAME)
    return RequestHeapFrameParams(
        bytes=parsed_data.args.bytes,
    )


def decode_set_compute_unit_limit(instruction: Instruction) -> SetComputeUnitLimitParams:
    """Decode a set_compute_unit_limit instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 0, InstructionType.SET_COMPUTE_UNIT_LIMIT)
    return SetComputeUnitLimitParams(
        units=parsed_data.args.units,
    )


def decode_set_compute_unit_price(instruction: Instruction) -> SetComputeUnitPriceParams:
    """Decode a set_compute_unit_price instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 0, InstructionType.SET_COMPUTE_UNIT_PRICE)
    return SetComputeUnitPriceParams(
        micro_lamports=parsed_data.args.micro_lamports,
    )


@deprecated("Use set_compute_unit_limit instead.")
def request_units(params: RequestUnitsParams) -> Instruction:
    """Creates a transaction instruction that requests units.

    Example:
        >>> params = RequestUnitsParams(units=150_000, additional_fee=0)
        >>> type(request_units(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to request units.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.REQUEST_UNITS,
            "args": {
                "units": params.units,
                "additional_fee": params.additional_fee,
            },
        }
    )
    return Instruction(
        accounts=[],
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
        data=data,
    )


def request_heap_frame(params: RequestHeapFrameParams) -> Instruction:
    """Creates a transaction instruction that requests heap frame.

    Example:
        >>> params = RequestHeapFrameParams(bytes=32_000 * 100) # 100 * 32K = 800 Compute Units
        >>> type(request_heap_frame(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to request heap frame.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.REQUEST_HEAP_FRAME,
            "args": {
                "bytes": params.bytes,
            },
        }
    )
    return Instruction(
        accounts=[],
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
        data=data,
    )


def set_compute_unit_limit(params: SetComputeUnitLimitParams) -> Instruction:
    """Creates a transaction instruction that sets the compute unit limit.

    By default, the compute budget is the product of 200,000 Compute Units (CU) * number of instructions,
    with a max of 1.4M CU.

    Example:
        >>> params = SetComputeUnitLimitParams(units=1_000_000)
        >>> type(set_compute_unit_limit(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to set the compute unit limit.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.SET_COMPUTE_UNIT_LIMIT,
            "args": {
                "units": params.units,
            },
        }
    )
    return Instruction(
        accounts=[],
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
        data=data,
    )


def set_compute_unit_price(params: SetComputeUnitPriceParams) -> Instruction:
    """Creates a transaction instruction that sets the compute unit price.

    For example: 1000 micro Lamports = 10^-12 SOL, so for an instruction that uses 150_000 compute units,
    the additional priority fee would be 150_000 * 1000 = 150_000_000 micro Lamports = 150 Lamports = 150 * 10^-9 SOL.

    Example:
        >>> params = SetComputeUnitPriceParams(micro_lamports=1_000)
        >>> type(set_compute_unit_price(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to set the compute unit price.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.SET_COMPUTE_UNIT_PRICE,
            "args": {
                "micro_lamports": params.micro_lamports,
            },
        }
    )
    return Instruction(
        accounts=[],
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
        data=data,
    )
