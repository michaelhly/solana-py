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
    decoded_params = spl_token.decode_initialize_mint(instruction)
    assert not decoded_params.freeze_authority
    assert decoded_params == params_no_freeze


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


def test_initialize_multisig():
    """Test initialize multisig."""
    new_multisig = PublicKey(0)
    signers = [PublicKey(i + 1) for i in range(3)]
    params = spl_token.InitializeMultisigParams(
        program_id=TOKEN_PROGRAM_ID,
        multisig=new_multisig,
        signers=signers,
        m=len(signers),
    )
    instruction = spl_token.initialize_multisig(params)
    assert spl_token.decode_initialize_multisig(instruction) == params


def test_transfer(stubbed_reciever, stubbed_sender):
    """Test transfer."""
    params = spl_token.TransferParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key(),
        destination=stubbed_reciever,
        owner=stubbed_sender.public_key(),
        signers=[],
        amount=123,
    )
    instruction = spl_token.transfer(params)
    assert spl_token.decode_transfer(instruction) == params

    multisig_params = spl_token.TransferParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key(),
        destination=stubbed_reciever,
        owner=stubbed_sender.public_key(),
        signers=[PublicKey(i + 1) for i in range(3)],
        amount=123,
    )
    instruction = spl_token.transfer(multisig_params)
    assert spl_token.decode_transfer(instruction) == multisig_params


def test_approve(stubbed_sender):
    """Test approve."""
    delegate_account = PublicKey(0)
    params = spl_token.ApproveParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key(),
        delegate=delegate_account,
        owner=stubbed_sender.public_key(),
        signers=[],
        amount=123,
    )
    instruction = spl_token.approve(params)
    assert spl_token.decode_approve(instruction) == params

    multisig_params = spl_token.ApproveParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key(),
        delegate=delegate_account,
        owner=stubbed_sender.public_key(),
        signers=[PublicKey(i + 1) for i in range(3)],
        amount=123,
    )
    instruction = spl_token.approve(multisig_params)
    assert spl_token.decode_approve(instruction) == multisig_params


def test_revoke(stubbed_sender):
    """Test revoke."""
    delegate_account = PublicKey(0)
    params = spl_token.RevokeParams(
        program_id=TOKEN_PROGRAM_ID,
        delegate=delegate_account,
        owner=stubbed_sender.public_key(),
        signers=[],
    )
    instruction = spl_token.revoke(params)
    assert spl_token.decode_revoke(instruction) == params

    multisig_params = spl_token.RevokeParams(
        program_id=TOKEN_PROGRAM_ID,
        delegate=delegate_account,
        owner=stubbed_sender.public_key(),
        signers=[PublicKey(i + 1) for i in range(3)],
    )
    instruction = spl_token.revoke(multisig_params)
    assert spl_token.decode_revoke(instruction) == multisig_params


def test_set_authority():
    """Test set authority."""
    account, new_authority, current_authority = PublicKey(0), PublicKey(1), PublicKey(2)
    params = spl_token.SetAuthorityParams(
        program_id=TOKEN_PROGRAM_ID,
        account=account,
        authority=spl_token.AuthorityType.FreezeAccount,
        new_authority=new_authority,
        current_authority=current_authority,
        signers=[],
    )
    instruction = spl_token.set_authority(params)
    assert spl_token.decode_set_authority(instruction) == params

    multisig_params = spl_token.SetAuthorityParams(
        program_id=TOKEN_PROGRAM_ID,
        account=account,
        authority=spl_token.AuthorityType.FreezeAccount,
        current_authority=current_authority,
        signers=[PublicKey(i + 1) for i in range(3, 10)],
    )
    instruction = spl_token.set_authority(multisig_params)
    decoded_params = spl_token.decode_set_authority(instruction)
    assert not decoded_params.new_authority
    assert decoded_params == multisig_params


def test_close_account(stubbed_sender):
    """Test close account."""
    token_account = PublicKey(0)
    params = spl_token.CloseAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        destination=stubbed_sender.public_key(),
        owner=stubbed_sender.public_key(),
        signers=[],
    )
    instruction = spl_token.close_account(params)
    assert spl_token.decode_close_account(instruction) == params

    multisig_params = spl_token.CloseAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        destination=stubbed_sender.public_key(),
        owner=stubbed_sender.public_key(),
        signers=[PublicKey(i + 1) for i in range(3)],
    )
    instruction = spl_token.close_account(multisig_params)
    assert spl_token.decode_close_account(instruction) == multisig_params
