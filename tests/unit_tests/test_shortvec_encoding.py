"""Unit tests for solana.utils.shortvec_encoding."""

from typing import List

from solana.utils.shortvec_encoding import decode_length, encode_length


def assert_decoded_array(raw_bytes: bytes, expected_length, expected_value: int):
    """Helper to check length and value of a decoded array."""
    value, length = decode_length(raw_bytes)
    assert value == expected_value
    assert length == expected_length


def test_decode_length():
    """Test decode length."""
    assert_decoded_array(bytes([]), 0, 0)
    assert_decoded_array(bytes([5]), 1, 5)
    assert_decoded_array(bytes([0x7F]), 1, 0x7F)
    assert_decoded_array(bytes([0x80, 0x01]), 2, 0x80)
    assert_decoded_array(bytes([0xFF, 0x01]), 2, 0xFF)
    assert_decoded_array(bytes([0x80, 0x02]), 2, 0x100)
    assert_decoded_array(bytes([0xFF, 0xFF, 0x01]), 3, 0x7FFF)
    assert_decoded_array(bytes([0x80, 0x80, 0x80, 0x01]), 4, 0x200000)


def assert_encoded_array(buffer: bytearray, length: int, prev_length: int, expected: List[int]) -> None:
    """Helper to encode length of an array."""
    assert len(buffer) == prev_length
    actual = encode_length(length)
    buffer.extend(actual)
    assert len(buffer) == prev_length + len(expected)
    assert bytes(buffer[-len(expected) :]) == bytes(expected)  # noqa: 203


def test_encode_length():
    """Test encode length."""
    buffer = bytearray()
    prev_length = 0

    expected = [0]
    assert_encoded_array(buffer, 0, prev_length, expected)
    prev_length += len(expected)

    expected = [5]
    assert_encoded_array(buffer, 5, prev_length, expected)
    prev_length += len(expected)

    expected = [0x7F]
    assert_encoded_array(buffer, 0x7F, prev_length, expected)
    prev_length += len(expected)

    expected = [0x80, 0x01]
    assert_encoded_array(buffer, 0x80, prev_length, expected)
    prev_length += len(expected)

    expected = [0xFF, 0x01]
    assert_encoded_array(buffer, 0xFF, prev_length, expected)
    prev_length += len(expected)

    expected = [0x80, 0x02]
    assert_encoded_array(buffer, 0x100, prev_length, expected)
    prev_length += len(expected)

    expected = [0xFF, 0xFF, 0x01]
    assert_encoded_array(buffer, 0x7FFF, prev_length, expected)
    prev_length += len(expected)

    expected = [
        0x80,
        0x80,
        0x80,
        0x01,
    ]
    assert_encoded_array(buffer, 0x200000, prev_length, expected)
    prev_length += len(expected)

    assert prev_length == len(buffer) == 16
