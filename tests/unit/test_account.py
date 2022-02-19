"""Unit tests for solana.account."""
from base64 import b64decode

from based58 import b58decode
from nacl.bindings import crypto_box_SECRETKEYBYTES  # type: ignore
from nacl.signing import VerifyKey  # type: ignore

from solana._layouts.account import VERSIONS_LAYOUT
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


def test_decode_nonce_account_data():
    b64_data = (
        "AAAAAAEAAADbpRzeSWD3B/Ei2SfSmwM6qTDlK5pCxRlx3Vsnr3+v14Bbu3aJmuW0cG"
        "J2BVvh7C9g5qNUM+I200HP5eSQ8MHBiBMAAAAAAAA="
    )

    raw_data = b64decode(b64_data)
    parsed = VERSIONS_LAYOUT.parse(raw_data)

    assert parsed.state.data.authority == b58decode(b"FnQK7qe8rkD3x2GrA8ERptTd7bp7KwqouvaQYtr1uuaE")
    assert parsed.state.data.blockhash == b58decode(b"9e4KCe4NTbA87aUVugjo6Yb1EVittdxy1RQu6AELCTL4")
    assert parsed.state.data.fee_calculator.lamports_per_signature == 5000
