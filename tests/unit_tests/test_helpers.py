"""Test helpers."""

from random import randint

import pytest

import solana.utils.helpers as helpers


def test_to_uint8_bytes():
    """Test int to uint8 bytes."""
    assert helpers.to_uint8_bytes(255) == b"\xff"
    with pytest.raises(OverflowError):
        helpers.to_uint8_bytes(256)


def test_from_uint8():
    """Test uint8 bytes to int."""
    num = randint(0, 255)
    assert helpers.from_uint8_bytes(helpers.to_uint8_bytes(num)) == num
