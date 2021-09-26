"""Unit tests for solana.account."""
from base58 import b58decode
from nacl.bindings import crypto_box_SECRETKEYBYTES  # type: ignore
from nacl.signing import VerifyKey  # type: ignore

from solana.account import Account


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
    assert str(acc.public_key()) == "2q7pyhPwAwZ3QMfZrnAbDhnh9mDUqycszcpf86VgQxhF"


def test_sign_message(stubbed_sender):
    """Test message signing."""
    msg = b"hello"
    signed_msg = stubbed_sender.sign(msg)
    assert VerifyKey(bytes(stubbed_sender.public_key)).verify(signed_msg.message, signed_msg.signature) == msg


def test_account_keypair():
    """Validate account keypair against account's private and public key."""
    expected_account = Account()
    keypair = expected_account.keypair()
    decoded_keypair = b58decode(keypair)

    actual_account = Account(decoded_keypair[:32])
    assert expected_account.public_key() == actual_account.public_key()
    assert expected_account.secret_key() == actual_account.secret_key()
