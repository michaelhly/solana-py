"""Unit tests for SPL-token instructions."""

import spl.token.instructions as spl_token
from solana.publickey import PublicKey
from spl.token.program import TOKEN_PROGRAM_ID


def test_initialize_mint(stubbed_sender):
    """Test initialize mint."""
    mint_authority, freeze_authority = PublicKey(0), PublicKey(1)
    params_with_freeze = spl_token.InitializeMintParams(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.public_key(),
        mint_authority=mint_authority,
        freeze_authority=freeze_authority,
    )
    instruction = spl_token.initialize_mint(params_with_freeze)
    assert spl_token.decode_initialize_mint(instruction) == params_with_freeze

    params_no_freeze = spl_token.InitializeMintParams(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.public_key(),
        mint_authority=mint_authority,
    )
    instruction = spl_token.initialize_mint(params_no_freeze)
    assert spl_token.decode_initialize_mint(instruction) == params_no_freeze


def test_initialize_account(stubbed_sender):
    """Test initialize account."""
    new_account, token_mint = PublicKey(0), PublicKey(1)
    params = spl_token.InitializeAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=new_account,
        mint=token_mint,
        owner=stubbed_sender.public_key(),
    )
    instruction = spl_token.initialize_account(params)
    assert spl_token.decode_initialize_account(instruction) == params
