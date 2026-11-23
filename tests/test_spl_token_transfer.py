import struct

import pytest


def serialize_spl_transfer(amount: int) -> bytes:
    """Serializes Solana SPL Transfer instruction with strict bounds checking."""
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("Amount must be an integer, not boolean.")
    if amount < 0:
        raise ValueError("SPL transfer amount cannot be negative.")
    if amount > 18_446_744_073_709_551_615:
        raise ValueError("SPL transfer amount exceeds u64 maximum.")
    return struct.pack("<BQ", 3, amount)


def test_valid_transfer_serialization():
    payload = serialize_spl_transfer(1_000_000)
    assert len(payload) == 9
    assert payload[0] == 3
    assert struct.unpack("<Q", payload[1:])[0] == 1_000_000


def test_zero_amount_transfer():
    payload = serialize_spl_transfer(0)
    assert payload == b"\x03\x00\x00\x00\x00\x00\x00\x00\x00"


def test_negative_amount_raises_error():
    with pytest.raises(ValueError, match="negative"):
        serialize_spl_transfer(-1)


def test_overflow_amount_raises_error():
    with pytest.raises(ValueError, match="exceeds u64"):
        serialize_spl_transfer(18_446_744_073_709_551_616)


def test_bool_amount_raises_type_error():
    with pytest.raises(TypeError, match="not boolean"):
        serialize_spl_transfer(True)
