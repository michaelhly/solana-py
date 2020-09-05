"""Validation utilities."""

from enum import IntEnum
from typing import Any


def validate_instruction_type(parsed_data: Any, expected_type: IntEnum) -> None:
    """Check that the instruction type of the parsed data matches the expected instruction type."""
    if parsed_data.instruction_type != expected_type:
        raise ValueError(
            f"invalid instruction; instruction index mismatch {parsed_data.instruction_type} != {expected_type}"
        )
