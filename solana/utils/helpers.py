"""Helper functions."""


def to_uint8(val: int) -> bytes:
    """Convert an integer to uint8."""
    return val.to_bytes(1, byteorder="big")
