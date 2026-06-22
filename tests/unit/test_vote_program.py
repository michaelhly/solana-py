"""Unit tests for solana.vote_program."""

import base64

import pytest
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
import solana.vote_program as vp
from solana import models


@pytest.mark.parametrize(
    "params_cls",
    [vp.WithdrawFromVoteAccountParams, models.WithdrawFromVoteAccountParams],
)
def test_withdraw_from_vote_account(params_cls):
    withdrawer_keypair = Keypair.from_bytes(
        [
            134,
            123,
            27,
            208,
            227,
            175,
            253,
            99,
            4,
            81,
            170,
            231,
            186,
            141,
            177,
            142,
            197,
            139,
            94,
            6,
            157,
            2,
            163,
            89,
            150,
            121,
            235,
            86,
            185,
            22,
            1,
            233,
            58,
            133,
            229,
            39,
            212,
            71,
            254,
            72,
            246,
            45,
            160,
            156,
            129,
            199,
            18,
            189,
            53,
            143,
            98,
            72,
            182,
            106,
            69,
            29,
            38,
            145,
            119,
            190,
            13,
            105,
            157,
            112,
        ]
    )
    vote_account_pubkey = Pubkey.from_string("CWqJy1JpmBcx7awpeANfrPk6AsQKkmego8ujjaYPGFEk")
    receiver_account_pubkey = Pubkey.from_string("A1V5gsis39WY42djdTKUFsgE5oamk4nrtg16WnKTuzZK")
    recent_blockhash = Hash.from_string("Add1tV7kJgNHhTtx3Dgs6dhC7kyXrGJQZ2tJGW15tLDH")
    msg = MessageV0.try_compile(
        payer=withdrawer_keypair.pubkey(),
        instructions=[
            vp.withdraw_from_vote_account(
                params_cls(
                    vote_account_from_pubkey=vote_account_pubkey,
                    to_pubkey=receiver_account_pubkey,
                    withdrawer=withdrawer_keypair.pubkey(),
                    lamports=2_000_000_000,
                )
            )
        ],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )

    # Generate this value with:
    # base64.b64encode(bytes(msg)).decode("ascii")
    expected_wire_msg = base64.b64decode(
        b"AQABBDqF5SfUR/5I9i2gnIHHEr01j2JItmpFHSaRd74NaZ1whdju9KDr87dR4CFbvp8kmkq1rSYitXg2nDzw1kcQsBarFQYO0flqHdOoQpaNxOZ8eSlkLWHns0kvxLHtDo6WbQdhSB01dHS7fE12JOvTvbPYNV5z0RBD/A2jU4AAAAAAjxrQaMS7FjmaR++mvFr3XE6XbzMUTMJUIpITrUWBzGwBAwMCAQAMAwAAAACUNXcAAAAAAA=="
    )

    serialized_message = bytes(msg)

    assert serialized_message
    assert serialized_message == expected_wire_msg
