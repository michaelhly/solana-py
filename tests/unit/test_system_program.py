"""Unit tests for solana.system_program."""
import solana.system_program as sp
from solana.account import Account
from solana.publickey import PublicKey


def test_create_account():
    """Test creating a transaction for create account."""
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
    """Test creating a transaction for assign."""
    params = sp.AssignParams(
        account_pubkey=Account().public_key(),
        program_id=PublicKey(1),
    )
    assert sp.decode_assign(sp.assign(params)) == params


def test_allocate():
    """Test creating a transaction for allocate."""
    params = sp.AllocateParams(
        account_pubkey=Account().public_key(),
        space=12345,
    )
    assert sp.decode_allocate(sp.allocate(params)) == params


def test_allocate_with_seed():
    """Test creating a transaction for allocate with seed."""
    params = sp.AllocateWithSeedParams(
        account_pubkey=Account().public_key(),
        base_pubkey=PublicKey(1),
        seed={"length": 4, "chars": "gqln"},
        space=65537,
        program_id=PublicKey(2),
    )
    assert sp.decode_allocate_with_seed(sp.allocate(params)) == params
