"""Helper functions."""


def from_uint8_bytes(uint8: bytes) -> int:
    """Convert from uint8 to python int."""
    return int.from_bytes(uint8, byteorder="little")


def to_uint8_bytes(val: int) -> bytes:
    """Convert an integer to uint8."""
    return val.to_bytes(1, byteorder="little")


def verify_instruction_keys(actual: int, expected: int) -> None:
    """Verify length of AccountMeta list is at least the expected length.

    :param actual: Actual length of AccountMetas list of an instruction.
    :param expected: Expected length.
    """
    if actual < expected:
        raise ValueError(f"invalid instruction: found {actual} keys, expected at least {expected}")
