"""Test helpers."""
import pytest

from solana.utils import helpers


def test_to_uint8_bytes():
    """Test int to uint8 bytes."""
    assert helpers.to_uint8_bytes(255) == b"\xff"
    with pytest.raises(OverflowError):
        helpers.to_uint8_bytes(256)
