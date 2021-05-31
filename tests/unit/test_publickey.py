"""Unit Tests for solana.publickey."""

import pytest

from solana.publickey import PublicKey
from solana.utils import helpers


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


def test_create_program_address():
    """Test create program address."""
    program_id = PublicKey("BPFLoader1111111111111111111111111111111111")
    program_address = PublicKey.create_program_address([bytes(), bytes([1])], program_id)
    assert program_address == PublicKey("3gF2KMe9KiC6FNVBmfg9i267aMPvK37FewCip4eGBFcT")

    program_address = PublicKey.create_program_address([bytes("☉", "utf-8")], program_id)
    assert program_address == PublicKey("7ytmC1nT1xY4RfxCV2ZgyA7UakC93do5ZdyhdF3EtPj7")

    seeds = [bytes("Talking", "utf8"), bytes("Squirrels", "utf8")]
    program_address = PublicKey.create_program_address(seeds, program_id)
    assert program_address == PublicKey("HwRVBufQ4haG5XSgpspwKtNd3PC9GM9m1196uJW36vds")

    program_address = PublicKey.create_program_address(
        [bytes(PublicKey("SeedPubey1111111111111111111111111111111111"))], program_id
    )
    assert program_address == PublicKey("GUs5qLUfsEHkcMB9T38vjr18ypEhRuNWiePW2LoK4E3K")

    program_address_2 = PublicKey.create_program_address([bytes("Talking", "utf8")], program_id)
    assert program_address_2 != program_address

    # https://github.com/solana-labs/solana/issues/11950
    seeds = [bytes(PublicKey("H4snTKK9adiU15gP22ErfZYtro3aqR9BTMXiH3AwiUTQ")), bytes.fromhex("0200000000000000")]
    program_address = PublicKey.create_program_address(seeds, PublicKey("4ckmDgGdxQoPDLUkDT3vHgSAkzA3QRdNq5ywwY4sUSJn"))
    assert program_address == PublicKey("12rqwuEgBYiGhBrDJStCiqEtzQpTTiZbh7teNVLuYcFA")


def test_find_program_address():
    """Test create associated_token_address."""
    program_id = PublicKey("BPFLoader1111111111111111111111111111111111")
    program_address, nonce = PublicKey.find_program_address([bytes()], program_id)
    assert program_address == PublicKey.create_program_address([bytes(), helpers.to_uint8_bytes(nonce)], program_id)


def test_is_on_curve():
    """Test on curve verify."""
    on_curve = PublicKey("4fwsi7ei2vDcUByZWXV3YmMEyLwBnLamiuDzUrEKADnm")
    assert PublicKey._is_on_curve(pubkey_bytes=bytes(on_curve))  # pylint: disable=protected-access

    off_curve = PublicKey("12rqwuEgBYiGhBrDJStCiqEtzQpTTiZbh7teNVLuYcFA")
    assert not PublicKey._is_on_curve(pubkey_bytes=bytes(off_curve))  # pylint: disable=protected-access


def test_create_with_seed():
    """Test create with seed"""
    default_public_key = PublicKey("11111111111111111111111111111111")
    derived_key = PublicKey.create_with_seed(default_public_key, "limber chicken: 4/45", default_public_key)
    assert derived_key == PublicKey("9h1HyLCW5dZnBVap8C5egQ9Z6pHyjsh5MNy83iPqqRuq")
