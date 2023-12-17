"""Library to interface with the compute budget program."""
from __future__ import annotations

from typing import NamedTuple

from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey

from solana._layouts.compute_budget_instructions import (
    COMPUTE_BUDGET_INSTRUCTIONS_LAYOUT,
    InstructionType,
)

COMPUTE_BUDGET_PROGRAM_ID: Pubkey = Pubkey.from_string("ComputeBudget111111111111111111111111111111")


# Instruction Params
class RequestUnitsDeprecatedParams(NamedTuple):
    """Request additional compute units for the current transaction."""

    units: int
    """Number of additional units to request."""
    additional_fee: int
    """Additional fee to pay for the units."""
    payer: Pubkey
    """Public key of the transaction payer."""


class RequestHeapFrameParams(NamedTuple):
    """Request additional heap frame for the current transaction."""

    value: int
    """Number of additional units to request."""
    payer: Pubkey
    """Public key of the transaction payer."""


class SetComputeUnitLimitParams(NamedTuple):
    """Set the compute unit limit for the current transaction."""

    value: int
    """Number of additional units to request."""
    payer: Pubkey
    """Public key of the transaction payer."""


class SetComputeUnitPriceParams(NamedTuple):
    """Set the compute unit price for the current transaction."""

    value: int
    """Number of additional units to request."""
    payer: Pubkey
    """Public key of the transaction payer."""


class SetLoadedAccountsDataSizeLimitParams(NamedTuple):
    """Set the loaded accounts data size limit for the current transaction."""

    value: int
    """Number of additional units to request."""
    payer: Pubkey
    """Public key of the transaction payer."""


def request_units_deprecated(_params: RequestUnitsDeprecatedParams) -> Instruction:
    """Generate an instruction that requests additional compute units for the current transaction.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> from solders.keypair import Keypair
        >>> payer = Keypair.from_seed(bytes([0]*32))
        >>> instruction = request_units_deprecated(
        ...    RequestUnitsDeprecatedParams(
        ...        units=400_000,
        ...        additional_fee=0,
        ...        payer=payer.pubkey(),
        ...    )
        ... )
        >>> type(instruction)
        <class 'solders.instruction.Instruction'>

    Returns:
        The generated and deprecated request units instruction.
    """
    # data = COMPUTE_BUDGET_INSTRUCTIONS_LAYOUT.build(
    #     {
    #         "instruction_type": InstructionType.REQUEST_UNITS_DEPRECATED,
    #         "args": {"units": params.units, "additional_fee": params.additional_fee},
    #     }
    # )

    # return Instruction(
    #     accounts=[
    #         AccountMeta(
    #             pubkey=params.payer,
    #             is_signer=True,
    #             is_writable=True,
    #         ),
    #     ],
    #     data=data,
    #     program_id=COMPUTE_BUDGET_PROGRAM_ID,
    # )

    raise NotImplementedError(
        "This is a deprecated instruction. Please use the set_compute_unit_limit instruction instead."
    )


def request_heap_frame(params: RequestHeapFrameParams) -> Instruction:
    """Generate an instruction that requests additional heap frame for the current transaction.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> from solders.keypair import Keypair
        >>> payer = Keypair.from_seed(bytes([0]*32))
        >>> instruction = request_heap_frame(
        ...    RequestHeapFrameParams(
        ...        value=1024 * 64,
        ...        payer=payer.pubkey(),
        ...    )
        ... )
        >>> type(instruction)
        <class 'solders.instruction.Instruction'>

    Returns:
        The generated request heap frame instruction.
    """
    data = COMPUTE_BUDGET_INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.REQUEST_HEAP_FRAME,
            "args": {"value": params.value},
        }
    )

    return Instruction(
        accounts=[
            AccountMeta(
                pubkey=params.payer,
                is_signer=True,
                is_writable=True,
            ),
        ],
        data=data,
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
    )


def set_compute_unit_limit(params: SetComputeUnitLimitParams) -> Instruction:
    """Generate an instruction that sets the compute unit limit for the current transaction.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> from solders.keypair import Keypair
        >>> payer = Keypair.from_seed(bytes([0]*32))
        >>> instruction = set_compute_unit_limit(
        ...    SetComputeUnitLimitParams(
        ...        value=100_000,
        ...        payer=payer.pubkey(),
        ...    )
        ... )
        >>> type(instruction)
        <class 'solders.instruction.Instruction'>

    Returns:
        The generated set compute unit limit instruction.
    """
    data = COMPUTE_BUDGET_INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.SET_COMPUTE_UNIT_LIMIT,
            "args": {"value": params.value},
        }
    )

    return Instruction(
        accounts=[
            AccountMeta(
                pubkey=params.payer,
                is_signer=True,
                is_writable=True,
            ),
        ],
        data=data,
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
    )


def set_compute_unit_price(params: SetComputeUnitPriceParams) -> Instruction:
    """Generate an instruction that sets the compute unit price for the current transaction.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> from solders.keypair import Keypair
        >>> payer = Keypair.from_seed(bytes([0]*32))
        >>> instruction = set_compute_unit_price(
        ...    SetComputeUnitPriceParams(
        ...        value=100,
        ...        payer=payer.pubkey(),
        ...    )
        ... )
        >>> type(instruction)
        <class 'solders.instruction.Instruction'>

    Returns:
        The generated set compute unit price instruction.
    """
    data = COMPUTE_BUDGET_INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.SET_COMPUTE_UNIT_PRICE,
            "args": {"value": params.value},
        }
    )

    return Instruction(
        accounts=[
            AccountMeta(
                pubkey=params.payer,
                is_signer=True,
                is_writable=True,
            ),
        ],
        data=data,
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
    )


def set_loaded_accounts_data_size_limit(params: SetLoadedAccountsDataSizeLimitParams) -> Instruction:
    """Generate an instruction that sets the loaded accounts data size limit for the current transaction.

    Example:
        >>> from solders.pubkey import Pubkey
        >>> from solders.keypair import Keypair
        >>> payer = Keypair.from_seed(bytes([0]*32))
        >>> instruction = set_loaded_accounts_data_size_limit(
        ...    SetLoadedAccountsDataSizeLimitParams(
        ...        value=10*1024*1024,
        ...        payer=payer.pubkey(),
        ...    )
        ... )
        >>> type(instruction)
        <class 'solders.instruction.Instruction'>

    Returns:
        The generated set loaded accounts data size limit instruction.
    """
    data = COMPUTE_BUDGET_INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.SET_LOADED_ACCOUNTS_DATA_SIZE_LIMIT,
            "args": {"value": params.value},
        }
    )

    return Instruction(
        accounts=[
            AccountMeta(
                pubkey=params.payer,
                is_signer=True,
                is_writable=True,
            ),
        ],
        data=data,
        program_id=COMPUTE_BUDGET_PROGRAM_ID,
    )
