"""Unit tests for solana.transaction."""
from base64 import b64decode, b64encode

import pytest
from based58 import b58encode

import solana.system_program as sp
import solana.transaction as txlib
from solana.keypair import Keypair
from solana.message import CompiledInstruction, Message, MessageArgs, MessageHeader
from solana.publickey import PublicKey


def test_sign_partial(stubbed_blockhash):
    """Test paritally sigining a transaction."""
    kp1, kp2 = Keypair(), Keypair()
    transfer = sp.transfer(sp.TransferParams(from_pubkey=kp1.public_key, to_pubkey=kp2.public_key, lamports=123))
    partial_txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
    partial_txn.sign_partial(kp1, kp2.public_key)
    assert len(partial_txn.signature()) == txlib.SIG_LENGTH
    assert len(partial_txn.signatures) == 2
    assert not partial_txn.signatures[1].signature

    partial_txn.add_signer(kp2)
    expected_txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
    expected_txn.sign(kp1, kp2)
    assert partial_txn == expected_txn


def test_transfer_signatures(stubbed_blockhash):
    """Test signing transfer transactions."""
    kp1, kp2 = Keypair(), Keypair()
    transfer1 = sp.transfer(sp.TransferParams(from_pubkey=kp1.public_key, to_pubkey=kp2.public_key, lamports=123))
    transfer2 = sp.transfer(sp.TransferParams(from_pubkey=kp2.public_key, to_pubkey=kp1.public_key, lamports=123))
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer1, transfer2)
    txn.sign(kp1, kp2)

    expected = txlib.Transaction(recent_blockhash=stubbed_blockhash, signatures=txn.signatures).add(
        transfer1, transfer2
    )
    assert txn == expected


def test_dedup_signatures(stubbed_blockhash):
    """Test signature deduplication."""
    kp1, kp2 = Keypair(), Keypair()
    transfer1 = sp.transfer(sp.TransferParams(from_pubkey=kp1.public_key, to_pubkey=kp2.public_key, lamports=123))
    transfer2 = sp.transfer(sp.TransferParams(from_pubkey=kp1.public_key, to_pubkey=kp2.public_key, lamports=123))
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer1, transfer2)
    txn.sign(kp1)


def test_wire_format_and_desrialize(stubbed_blockhash, stubbed_receiver, stubbed_sender):
    """Test serialize/derialize transaction to/from wire format."""
    transfer = sp.transfer(
        sp.TransferParams(from_pubkey=stubbed_sender.public_key, to_pubkey=stubbed_receiver, lamports=49)
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


def test_populate(stubbed_blockhash):
    """Test populating transaction with a message and two signatures."""
    account_keys = [str(PublicKey(i + 1)) for i in range(5)]
    msg = Message(
        MessageArgs(
            account_keys=account_keys,
            header=MessageHeader(
                num_readonly_signed_accounts=0, num_readonly_unsigned_accounts=3, num_required_signatures=2
            ),
            instructions=[CompiledInstruction(accounts=[1, 2, 3], data=b58encode(bytes([9] * 5)), program_id_index=4)],
            recent_blockhash=stubbed_blockhash,
        )
    )
    signatures = [b58encode(bytes([1] * txlib.SIG_LENGTH)), b58encode(bytes([2] * txlib.SIG_LENGTH))]
    transaction = txlib.Transaction.populate(msg, signatures)
    assert len(transaction.instructions) == len(msg.instructions)
    assert len(transaction.signatures) == len(signatures)
    assert transaction.recent_blockhash == msg.recent_blockhash


def test_serialize_unsigned_transaction(stubbed_blockhash, stubbed_receiver, stubbed_sender):
    """Test to serialize an unsigned transaction."""
    transfer = sp.transfer(
        sp.TransferParams(from_pubkey=stubbed_sender.public_key, to_pubkey=stubbed_receiver, lamports=49)
    )
    txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
    assert len(txn.signatures) == 0
    # Empty signature array fails
    with pytest.raises(AttributeError):
        txn.serialize()
    assert len(txn.signatures) == 0

    # Set fee payer
    txn.fee_payer = stubbed_sender.public_key
    # Serialize message
    assert b64encode(txn.serialize_message()) == (
        b"AQABAxOY9ixtGkV8UbpqS189vS9p/KkyFiGNyJl+QWvRfZPK/UOfzLZnJ/KJxcbeO8So/l3V13dwvI/xXD7u3LFK8/wAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMSa53YDeCBU8Xqd7OpDtETroO2xLG8dMcbg5KhL8FLrAQICAAEMAgAAADEAAAAAAAAA"
    )
    assert len(txn.instructions) == 1
    # Signature array populated with null signatures fails
    with pytest.raises(AttributeError):
        txn.serialize()
    assert len(txn.signatures) == 1
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
