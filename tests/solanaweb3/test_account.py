"""Unit tests for solanaweb3.account."""
from nacl.bindings import crypto_box_SECRETKEYBYTES  # type: ignore

from solanaweb3.account import Account


def test_generate_account():
    """Generate an account."""
    acc = Account()
    assert len(acc.secret_key()) == crypto_box_SECRETKEYBYTES


def test_generate_account_from_secret_key():
    """Generate an account with provided secret key."""
    secret_key = bytes(
        [
            153,
            218,
            149,
            89,
            225,
            94,
            145,
            62,
            233,
            171,
            46,
            83,
            227,
            223,
            173,
            87,
            93,
            163,
            59,
            73,
            190,
            17,
            37,
            187,
            146,
            46,
            51,
            73,
            79,
            73,
            136,
            40,
        ]
    )
    acc = Account(secret_key)
    assert str(acc.public_key()) == "93r5SeqYNetvTSzT7EkFBbReH4rfAYmGGTagYrkys73i"
