"""Unit tests for solana.system_program."""
import solana.system_program as sp
from solana.account import Account
from solana.publickey import PublicKey


def test_create_account():
    """Test creating a transaction for creat account."""
    params = sp.CreateAccountParams(
        from_pubkey=Account().public_key(),
        new_account_pubkey=Account().public_key(),
        lamports=123,
        space=1,
        program_id=PublicKey(1),
    )
    assert sp.decode_create_account(sp.create_account(params)) == params


def test_transfer():
    """Test creating a transaction for transfer."""
    params = sp.TransferParams(from_pubkey=Account().public_key(), to_pubkey=Account().public_key(), lamports=123)
    assert sp.decode_transfer(sp.transfer(params)) == params


def test_assign():
    """Test creating a transaction for transfer."""
    params = sp.AssignParams(
        account_pubkey=Account().public_key(),
        program_id=PublicKey(1),
    )
    assert sp.decode_assign(sp.assign(params)) == params
