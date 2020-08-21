"""Unit tests for solanaweb3.transaction"""
from base58 import b58encode

import solanaweb3.transaction as txlib
from solanaweb3.message import CompiledInstruction, Message, MessageArgs, MessageHeader
from solanaweb3.publickey import PublicKey


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
