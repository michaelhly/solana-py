"""Helper functions."""


def from_uint8_bytes(uint8: bytes) -> int:
    """Convert from uint8 to python int."""
    return int.from_bytes(uint8, byteorder="little")


def to_uint8_bytes(val: int) -> bytes:
    """Convert an integer to uint8."""
    return val.to_bytes(1, byteorder="little")
