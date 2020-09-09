"""Validation utilities."""
from __future__ import annotations

from enum import IntEnum
from typing import Any

from solana.transaction import TransactionInstruction


def validate_instruction_keys(instruction: TransactionInstruction, expected: int) -> None:
    """Verify length of AccountMeta list of a transaction instruction is at least the expected length.

    :param instruction: A TransactionInstruction object.
    :param expected: The expected length.
    """
    if len(instruction.keys) < expected:
        raise ValueError(f"invalid instruction: found {len(instruction.keys)} keys, expected at least {expected}")


def validate_instruction_type(parsed_data: Any, expected_type: IntEnum) -> None:
    """Check that the instruction type of the parsed data matches the expected instruction type.

    :param instruction: Parsed instruction data object with `instruction_type` field.
    :param expected_type: The expected instruction type.
    """
    if parsed_data.instruction_type != expected_type:
        raise ValueError(
            f"invalid instruction; instruction index mismatch {parsed_data.instruction_type} != {expected_type}"
        )
