"""Unit Tests for solana.publickey."""

import pytest

from solana.publickey import PublicKey


def test_invalid_pubkeys():
    """Test invalid public keys."""
    with pytest.raises(ValueError):
        PublicKey(
            [
                3,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ]
        )
    with pytest.raises(ValueError):
        PublicKey("0x300000000000000000000000000000000000000000000000000000000000000000000")
    with pytest.raises(ValueError):
        PublicKey("0x300000000000000000000000000000000000000000000000000000000000000")
    with pytest.raises(ValueError):
        PublicKey("135693854574979916511997248057056142015550763280047535983739356259273198796800000")
    with pytest.raises(ValueError):
        PublicKey("12345")


def test_equals():
    """Test public key equality."""
    array_key = PublicKey(
        [
            3,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    )
    base58_key = PublicKey("CiDwVBFgWV9E5MvXWoLgnEgn2hK7rJikbvfWavzAQz3")
    assert array_key == base58_key


def test_to_base58():
    """Test public key to base58."""
    key = PublicKey("CiDwVBFgWV9E5MvXWoLgnEgn2hK7rJikbvfWavzAQz3")
    assert key.to_base58() == b"CiDwVBFgWV9E5MvXWoLgnEgn2hK7rJikbvfWavzAQz3"
    assert str(key) == "CiDwVBFgWV9E5MvXWoLgnEgn2hK7rJikbvfWavzAQz3"
    key = PublicKey("1111111111111111111111111111BukQL")
    assert key.to_base58() == b"1111111111111111111111111111BukQL"
    assert str(key) == "1111111111111111111111111111BukQL"
    key = PublicKey("11111111111111111111111111111111")
    assert key.to_base58() == b"11111111111111111111111111111111"
    key = PublicKey(
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    )
    assert key.to_base58() == b"11111111111111111111111111111111"


def test_to_bytes():
    """Test public key to byte form."""
    key = PublicKey("CiDwVBFgWV9E5MvXWoLgnEgn2hK7rJikbvfWavzAQz3")
    assert len(bytes(key)) == PublicKey.LENGTH
    assert bytes(key) == (
        b"\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    key = PublicKey("11111111111111111111111111111111")
    assert len(bytes(key)) == PublicKey.LENGTH
    assert bytes(key) == (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    key = PublicKey(0)
    assert len(bytes(key)) == PublicKey.LENGTH
    assert bytes(key) == (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )


def test_equal_2():
    """Test public key equality (II)."""
    key_one = PublicKey(
        [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
        ]
    )
    key_two = PublicKey(bytes(key_one))
    assert key_one == key_two
