"""Unit tests for solana.vote_program."""
import base64

import solana.vote_program as vp
import solana.transaction as txlib
from solana.keypair import Keypair
from solana.publickey import PublicKey


def test_withdraw_from_vote_account():
    withdrawer_keypair = Keypair.from_secret_key(
        bytes(
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
    )
    vote_account_pubkey = PublicKey("CWqJy1JpmBcx7awpeANfrPk6AsQKkmego8ujjaYPGFEk")
    receiver_account_pubkey = PublicKey("A1V5gsis39WY42djdTKUFsgE5oamk4nrtg16WnKTuzZK")

    # solana withdraw-from-vote-account --dump-transaction-message \
    #   CWqJy1JpmBcx7awpeANfrPk6AsQKkmego8ujjaYPGFEk A1V5gsis39WY42djdTKUFsgE5oamk4nrtg16WnKTuzZK \
    # --authorized-withdrawer withdrawer.json \
    # 2 \
    # --blockhash Add1tV7kJgNHhTtx3Dgs6dhC7kyXrGJQZ2tJGW15tLDH \
    # --sign-only -k withdrawer.json
    wire_msg = base64.b64decode(
        b"AQABBDqF5SfUR/5I9i2gnIHHEr01j2JItmpFHSaRd74NaZ1wqxUGDtH5ah3TqEKWjcTmfHkpZC1h57NJL8Sx7Q6Olm2F2O70oOvzt1HgIVu+nySaSrWtJiK1eDacPPDWRxCwFgdhSB01dHS7fE12JOvTvbPYNV5z0RBD/A2jU4AAAAAAjxrQaMS7FjmaR++mvFr3XE6XbzMUTMJUIpITrUWBzGwBAwMBAgAMAwAAAACUNXcAAAAA"  # noqa: E501 pylint: disable=line-too-long
    )

    txn = txlib.Transaction(fee_payer=withdrawer_keypair.public_key)
    txn.recent_blockhash = "Add1tV7kJgNHhTtx3Dgs6dhC7kyXrGJQZ2tJGW15tLDH"

    txn.add(
        vp.withdraw_from_vote_account(
            vp.WithdrawFromVoteAccountParams(
                vote_account_from_pubkey=vote_account_pubkey,
                to_pubkey=receiver_account_pubkey,
                withdrawer=withdrawer_keypair.public_key,
                lamports=2_000_000_000,
            )
        )
    )

    serialized_message = txn.serialize_message()
    assert serialized_message == wire_msg
