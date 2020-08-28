"""Unit tests for solana.system_program."""
import solana.system_program as sp
from solana.account import Account


def test_transfer():
    """Test creating a transaction for transfer."""
    params = sp.TransferParams(from_pubkey=Account().public_key(), to_pubkey=Account().public_key(), lamports=123)
    txn = sp.transfer(params)
    assert len(txn.instructions) == 1
    assert sp.decode_transfer(txn.instructions[0]) == params
