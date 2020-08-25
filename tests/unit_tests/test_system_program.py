"""Unit tests for solanaweb3.system_program."""
import solana.system_program as sp
from solana.account import Account


def test_transfer():
    """Test creating a transaction for transfer."""
    params = sp.TransferParams(from_pubkey=Account().public_key(), to_pubkey=Account().public_key(), lamports=123)
    txn = sp.SystemProgram.transfer(params)
    assert len(txn.instructions) == 1
    assert sp.SystemInstruction.decode_transfer(txn.instructions[0]) == params
