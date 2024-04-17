"""Unit tests for solana.transaction."""
from base64 import b64decode, b64encode

import pytest
import solders.system_program as sp
from solders.hash import Hash as Blockhash
from solders.instruction import AccountMeta, CompiledInstruction
from solders.keypair import Keypair
from solders.message import Message
from solders.message import Message as SoldersMessage
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction import Transaction as SoldersTx

import solana.transaction as txlib


def example_tx(stubbed_blockhash, kp0: Keypair, kp1: Keypair, kp2: Keypair) -> txlib.Transaction:
    """Example tx for testing."""
    ixn = txlib.Instruction(
        program_id=Pubkey.default(),
        data=bytes([0, 0, 0, 0]),
        accounts=[
            AccountMeta(kp0.pubkey(), True, True),
            AccountMeta(kp1.pubkey(), True, True),
            AccountMeta(kp2.pubkey(), True, True),
        ],
    )
    return txlib.Transaction(fee_payer=kp0.pubkey(), instructions=[ixn], recent_blockhash=stubbed_blockhash)


def test_to_solders(stubbed_blockhash: Blockhash) -> None:
    """Test converting a Transaction to solders."""
    kp1, kp2 = Keypair(), Keypair()
    transfer = sp.transfer(sp.TransferParams(from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123))
    solders_transfer = sp.transfer(sp.TransferParams(from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123))
    assert transfer.data == solders_transfer.data
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
    solders_msg = SoldersMessage.new_with_blockhash([solders_transfer], None, stubbed_blockhash)
    solders_txn = SoldersTx.new_unsigned(solders_msg)
    assert txn.to_solders() == solders_txn
    assert txlib.Transaction.from_solders(solders_txn) == txn


def test_sign_partial(stubbed_blockhash):
    """Test partially sigining a transaction."""
    keypair0 = Keypair()
    keypair1 = Keypair()
    keypair2 = Keypair()
    ixn = txlib.Instruction(
        program_id=Pubkey.default(),
        data=bytes([0, 0, 0, 0]),
        accounts=[
            AccountMeta(keypair0.pubkey(), True, True),
            AccountMeta(keypair1.pubkey(), True, True),
            AccountMeta(keypair2.pubkey(), True, True),
        ],
    )
    txn = txlib.Transaction(fee_payer=keypair0.pubkey(), instructions=[ixn], recent_blockhash=stubbed_blockhash)
    assert txn.to_solders().message.header.num_required_signatures == 3
    txn.sign_partial(keypair0, keypair2)
    assert not txn.to_solders().is_signed()
    txn.sign_partial(keypair1)
    assert txn.to_solders().is_signed()
    expected_tx = txlib.Transaction(fee_payer=keypair0.pubkey(), instructions=[ixn], recent_blockhash=stubbed_blockhash)
    expected_tx.sign(keypair0, keypair1, keypair2)
    assert txn == expected_tx


def test_recent_blockhash_setter(stubbed_blockhash):
    """Test the recent_blockhash setter property works."""
    kp0, kp1, kp2 = Keypair(), Keypair(), Keypair()
    tx0 = example_tx(stubbed_blockhash, kp0, kp1, kp2)
    tx1 = example_tx(stubbed_blockhash, kp0, kp1, kp2)
    tx1.recent_blockhash = tx0.recent_blockhash
    assert tx0 == tx1


def test_transfer_signatures(stubbed_blockhash):
    """Test signing transfer transactions."""
    kp1, kp2 = Keypair(), Keypair()
    transfer1 = sp.transfer(sp.TransferParams(from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123))
    transfer2 = sp.transfer(sp.TransferParams(from_pubkey=kp2.pubkey(), to_pubkey=kp1.pubkey(), lamports=123))
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash)
    txn.add(transfer1, transfer2)
    txn.sign(kp1, kp2)

    expected = txlib.Transaction.populate(txn.compile_message(), txn.signatures)
    assert txn == expected


def test_dedup_signatures(stubbed_blockhash):
    """Test signature deduplication."""
    kp1, kp2 = Keypair(), Keypair()
    transfer1 = sp.transfer(sp.TransferParams(from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123))
    transfer2 = sp.transfer(sp.TransferParams(from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123))
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer1, transfer2)
    txn.sign(kp1)


def test_wire_format_and_desrialize(stubbed_blockhash, stubbed_receiver, stubbed_sender):
    """Test serialize/derialize transaction to/from wire format."""
    transfer = sp.transfer(
        sp.TransferParams(from_pubkey=stubbed_sender.pubkey(), to_pubkey=stubbed_receiver, lamports=49)
    )
    expected_txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
    expected_txn.sign(stubbed_sender)
    wire_txn = b64decode(
        b"AVuErQHaXv0SG0/PchunfxHKt8wMRfMZzqV0tkC5qO6owYxWU2v871AoWywGoFQr4z+q/7mE8lIufNl/kxj+nQ0BAAEDE5j2"
        b"LG0aRXxRumpLXz29L2n8qTIWIY3ImX5Ba9F9k8r9Q5/Mtmcn8onFxt47xKj+XdXXd3C8j/FcPu7csUrz/AAAAAAAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAxJrndgN4IFTxep3s6kO0ROug7bEsbx0xxuDkqEvwUusBAgIAAQwCAAAAMQAAAAAAAAA="
    )
    txn = txlib.Transaction.deserialize(wire_txn)
    assert txn == expected_txn
    assert wire_txn == expected_txn.serialize()


def test_populate():
    """Test populating transaction with a message and two signatures."""
    account_keys = [Pubkey([0] * 31 + [i + 1]) for i in range(5)]
    msg = Message.new_with_compiled_instructions(
        num_required_signatures=2,
        num_readonly_signed_accounts=0,
        num_readonly_unsigned_accounts=3,
        account_keys=account_keys,
        instructions=[CompiledInstruction(accounts=bytes([1, 2, 3]), data=bytes([9] * 5), program_id_index=4)],
        recent_blockhash=Blockhash.default(),
    )
    signatures = [Signature(bytes([1] * Signature.LENGTH)), Signature(bytes([2] * Signature.LENGTH))]
    transaction = txlib.Transaction.populate(msg, signatures)
    assert len(transaction.instructions) == len(msg.instructions)
    assert len(transaction.signatures) == len(signatures)
    assert transaction.recent_blockhash == msg.recent_blockhash


def test_serialize_unsigned_transaction(stubbed_blockhash, stubbed_receiver, stubbed_sender):
    """Test to serialize an unsigned transaction."""
    transfer = sp.transfer(
        sp.TransferParams(from_pubkey=stubbed_sender.pubkey(), to_pubkey=stubbed_receiver, lamports=49)
    )
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
    assert txn.signatures == (Signature.default(),)
    # Empty signature array fails
    with pytest.raises(AttributeError):
        txn.serialize()
    assert txn.signatures == (Signature.default(),)

    # Set fee payer
    txn.fee_payer = stubbed_sender.pubkey()
    # Serialize message
    assert b64encode(txn.serialize_message()) == (
        b"AQABAxOY9ixtGkV8UbpqS189vS9p/KkyFiGNyJl+QWvRfZPK/UOfzLZnJ/KJxcbeO8So/l3V13dwvI/xXD7u3LFK8/wAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMSa53YDeCBU8Xqd7OpDtETroO2xLG8dMcbg5KhL8FLrAQICAAEMAgAAADEAAAAAAAAA"
    )
    assert len(txn.instructions) == 1
    # Signature array populated with null signatures fails
    with pytest.raises(AttributeError):
        txn.serialize()
    assert txn.signatures == (Signature.default(),)
    # Properly signed transaction succeeds
    txn.sign(stubbed_sender)
    assert len(txn.instructions) == 1
    expected_serialization = b64decode(
        b"AVuErQHaXv0SG0/PchunfxHKt8wMRfMZzqV0tkC5qO6owYxWU2v871AoWywGoFQr4z+q/7mE8lIufNl/kxj+nQ0BAAEDE5j2"
        b"LG0aRXxRumpLXz29L2n8qTIWIY3ImX5Ba9F9k8r9Q5/Mtmcn8onFxt47xKj+XdXXd3C8j/FcPu7csUrz/AAAAAAAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAxJrndgN4IFTxep3s6kO0ROug7bEsbx0xxuDkqEvwUusBAgIAAQwCAAAAMQAAAAAAAAA="
    )
    assert txn.serialize() == expected_serialization
    assert len(txn.signatures) == 1
    assert txn.signatures != (Signature.default(),)


def test_serialize_unsigned_transaction_without_verifying_signatures(
    stubbed_blockhash, stubbed_receiver, stubbed_sender
):
    """Test to serialize an unsigned transaction without verifying the signatures."""
    transfer = sp.transfer(
        sp.TransferParams(from_pubkey=stubbed_sender.pubkey(), to_pubkey=stubbed_receiver, lamports=49)
    )
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
    assert txn.signatures == (Signature.default(),)

    # empty signatures should not fail
    txn.serialize(verify_signatures=False)
    assert txn.signatures == (Signature.default(),)

    # Set fee payer
    txn.fee_payer = stubbed_sender.pubkey()
    # Serialize message
    assert b64encode(txn.serialize_message()) == (
        b"AQABAxOY9ixtGkV8UbpqS189vS9p/KkyFiGNyJl+QWvRfZPK/UOfzLZnJ/KJxcbeO8So/l3V13dwvI/xXD7u3LFK8/wAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMSa53YDeCBU8Xqd7OpDtETroO2xLG8dMcbg5KhL8FLrAQICAAEMAgAAADEAAAAAAAAA"
    )
    assert len(txn.instructions) == 1
    # Signature array populated with null signatures should not fail
    txn.serialize(verify_signatures=False)
    assert txn.signatures == (Signature.default(),)


def test_sort_account_metas(stubbed_blockhash):
    """Test AccountMeta sorting after calling Transaction.compile_message()."""
    # S6EA7XsNyxg4yx4DJRMm7fP21jgZb1fuzBAUGhgVtkP
    signer_one = Keypair.from_seed(
        bytes(
            [
                216,
                214,
                184,
                213,
                199,
                75,
                129,
                160,
                237,
                96,
                96,
                228,
                46,
                251,
                146,
                3,
                71,
                162,
                37,
                117,
                121,
                70,
                143,
                16,
                128,
                78,
                53,
                189,
                222,
                230,
                165,
                249,
            ]
        )
    )

    # BKdt9U6V922P17ui81dzLoqgSY2B5ds1UD13rpwFB2zi
    receiver_one = Keypair.from_seed(
        bytes(
            [
                3,
                140,
                94,
                243,
                0,
                38,
                92,
                138,
                52,
                79,
                153,
                83,
                42,
                236,
                220,
                82,
                227,
                187,
                101,
                104,
                126,
                159,
                103,
                100,
                29,
                183,
                242,
                68,
                144,
                184,
                114,
                211,
            ]
        )
    )

    # DtDZCnXEN69n5W6rN5SdJFgedrWdK8NV9bsMiJekNRyu
    signer_two = Keypair.from_seed(
        bytes(
            [
                177,
                182,
                154,
                154,
                5,
                145,
                253,
                138,
                211,
                126,
                222,
                195,
                21,
                64,
                117,
                211,
                225,
                47,
                115,
                31,
                247,
                242,
                80,
                195,
                38,
                8,
                236,
                155,
                255,
                27,
                20,
                142,
            ]
        )
    )

    # FXgds3n6SNCoVVV4oELSumv8nKzAfqSgmeu7cNPikKFT
    receiver_two = Keypair.from_seed(
        bytes(
            [
                180,
                204,
                139,
                131,
                244,
                6,
                180,
                121,
                191,
                193,
                45,
                109,
                198,
                50,
                163,
                140,
                34,
                4,
                172,
                76,
                129,
                45,
                194,
                83,
                192,
                112,
                76,
                58,
                32,
                174,
                49,
                248,
            ]
        )
    )

    # C2UwQHqJ3BmEJHSMVmrtZDQGS2fGv8fZrWYGi18nHF5k
    signer_three = Keypair.from_seed(
        bytes(
            [
                29,
                79,
                73,
                16,
                137,
                117,
                183,
                2,
                131,
                0,
                209,
                142,
                134,
                100,
                190,
                35,
                95,
                220,
                200,
                163,
                247,
                237,
                161,
                70,
                226,
                223,
                100,
                148,
                49,
                202,
                154,
                180,
            ]
        )
    )

    # 8YPqwYXZtWPd31puVLEUPamS4wTv6F89n8nXDA5Ce2Bg
    receiver_three = Keypair.from_seed(
        bytes(
            [
                167,
                102,
                49,
                166,
                202,
                0,
                132,
                182,
                239,
                182,
                252,
                59,
                25,
                103,
                76,
                217,
                65,
                215,
                210,
                159,
                168,
                50,
                10,
                229,
                144,
                231,
                221,
                74,
                182,
                161,
                52,
                193,
            ]
        )
    )

    fee_payer = signer_one
    sorted_signers = sorted([x.pubkey() for x in [signer_one, signer_two, signer_three]], key=str)
    sorted_signers_excluding_fee_payer = [x for x in sorted_signers if str(x) != str(fee_payer.pubkey())]
    sorted_receivers = sorted([x.pubkey() for x in [receiver_one, receiver_two, receiver_three]], key=str)

    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash)
    txn.fee_payer = fee_payer.pubkey()

    # Add three transfer transactions
    txn.add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=signer_one.pubkey(),
                to_pubkey=receiver_one.pubkey(),
                lamports=2_000_000,
            )
        )
    )
    txn.add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=signer_two.pubkey(),
                to_pubkey=receiver_two.pubkey(),
                lamports=2_000_000,
            )
        )
    )
    txn.add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=signer_three.pubkey(),
                to_pubkey=receiver_three.pubkey(),
                lamports=2_000_000,
            )
        )
    )

    tx_msg = txn.compile_message()

    js_msg_b64_check = b"AwABBwZtbiRMvgQjcE2kVx9yon8XqPSO5hwc2ApflnOZMu0Qo9G5/xbhB0sp8/03Rv9x4MKSkQ+k4LB6lNLvCgKZ/ju/aw+EyQpTObVa3Xm+NA1gSTzutgFCTfkDto/0KtuIHHAMpKRb92NImxKeWQJ2/291j6nTzFj1D6nW25p7TofHmVsGt8uFnTv7+8vsWZ0uN7azdxa+jCIIm4WzKK+4uKfX39t5UA7S1soBQaJkTGOQkSbBo39gIjDkbW0TrevslgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAxJrndgN4IFTxep3s6kO0ROug7bEsbx0xxuDkqEvwUusDBgIABAwCAAAAgIQeAAAAAAAGAgIFDAIAAACAhB4AAAAAAAYCAQMMAgAAAICEHgAAAAAA"  # noqa: E501 pylint: disable=line-too-long

    assert b64encode(bytes(tx_msg)) == js_msg_b64_check

    # Transaction should organize AccountMetas by pubkey
    assert tx_msg.account_keys[0] == fee_payer.pubkey()
    assert tx_msg.account_keys[1] == sorted_signers_excluding_fee_payer[0]
    assert tx_msg.account_keys[2] == sorted_signers_excluding_fee_payer[1]
    assert tx_msg.account_keys[3] == sorted_receivers[0]
    assert tx_msg.account_keys[4] == sorted_receivers[1]
    assert tx_msg.account_keys[5] == sorted_receivers[2]
