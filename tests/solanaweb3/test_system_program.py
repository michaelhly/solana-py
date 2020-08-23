"""Unit tests for solanaweb3.system_program."""
import solanaweb3.system_program as splib
from solanaweb3.account import Account


def test_transfer():
    """Test creating a transaction for transfer."""
    params = splib.TransferParams(from_pubkey=Account().public_key(), to_pubkey=Account().public_key(), lamports=123)
    txn = splib.SystemProgram.transfer(params)
    assert len(txn.instructions) == 1
    assert splib.SystemInstruction.decode_transfer(txn.instructions[0]) == params
