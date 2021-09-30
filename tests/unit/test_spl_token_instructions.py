"""Unit tests for SPL-token instructions."""

import spl.token.instructions as spl_token
from solana.publickey import PublicKey
from spl.token.constants import TOKEN_PROGRAM_ID


def test_initialize_mint(stubbed_sender):
    """Test initialize mint."""
    mint_authority, freeze_authority = PublicKey(0), PublicKey(1)
    params_with_freeze = spl_token.InitializeMintParams(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.public_key,
        mint_authority=mint_authority,
        freeze_authority=freeze_authority,
    )
    instruction = spl_token.initialize_mint(params_with_freeze)
    assert spl_token.decode_initialize_mint(instruction) == params_with_freeze

    params_no_freeze = spl_token.InitializeMintParams(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.public_key,
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
        owner=stubbed_sender.public_key,
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


def test_transfer(stubbed_receiver, stubbed_sender):
    """Test transfer."""
    params = spl_token.TransferParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key,
        dest=stubbed_receiver,
        owner=stubbed_sender.public_key,
        amount=123,
    )
    instruction = spl_token.transfer(params)
    assert spl_token.decode_transfer(instruction) == params

    multisig_params = spl_token.TransferParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key,
        dest=stubbed_receiver,
        owner=stubbed_sender.public_key,
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
        source=stubbed_sender.public_key,
        delegate=delegate_account,
        owner=stubbed_sender.public_key,
        amount=123,
    )
    instruction = spl_token.approve(params)
    assert spl_token.decode_approve(instruction) == params

    multisig_params = spl_token.ApproveParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key,
        delegate=delegate_account,
        owner=stubbed_sender.public_key,
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
        account=delegate_account,
        owner=stubbed_sender.public_key,
    )
    instruction = spl_token.revoke(params)
    assert spl_token.decode_revoke(instruction) == params

    multisig_params = spl_token.RevokeParams(
        program_id=TOKEN_PROGRAM_ID,
        account=delegate_account,
        owner=stubbed_sender.public_key,
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
        authority=spl_token.AuthorityType.FREEZE_ACCOUNT,
        new_authority=new_authority,
        current_authority=current_authority,
    )
    instruction = spl_token.set_authority(params)
    assert spl_token.decode_set_authority(instruction) == params

    multisig_params = spl_token.SetAuthorityParams(
        program_id=TOKEN_PROGRAM_ID,
        account=account,
        authority=spl_token.AuthorityType.FREEZE_ACCOUNT,
        current_authority=current_authority,
        signers=[PublicKey(i) for i in range(3, 10)],
    )
    instruction = spl_token.set_authority(multisig_params)
    decoded_params = spl_token.decode_set_authority(instruction)
    assert not decoded_params.new_authority
    assert decoded_params == multisig_params


def test_mint_to(stubbed_receiver):
    """Test mint to."""
    mint, mint_authority = PublicKey(0), PublicKey(1)
    params = spl_token.MintToParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        dest=stubbed_receiver,
        mint_authority=mint_authority,
        amount=123,
    )
    instruction = spl_token.mint_to(params)
    assert spl_token.decode_mint_to(instruction) == params

    multisig_params = spl_token.MintToParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        dest=stubbed_receiver,
        mint_authority=mint_authority,
        signers=[PublicKey(i) for i in range(3, 10)],
        amount=123,
    )
    instruction = spl_token.mint_to(multisig_params)
    assert spl_token.decode_mint_to(instruction) == multisig_params


def test_burn(stubbed_receiver):
    """Test burn."""
    mint, owner = PublicKey(0), PublicKey(1)
    params = spl_token.BurnParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        account=stubbed_receiver,
        owner=owner,
        amount=123,
    )
    instruction = spl_token.burn(params)
    assert spl_token.decode_burn(instruction) == params

    multisig_params = spl_token.BurnParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        account=stubbed_receiver,
        owner=owner,
        signers=[PublicKey(i) for i in range(3, 10)],
        amount=123,
    )
    instruction = spl_token.burn(multisig_params)
    assert spl_token.decode_burn(instruction) == multisig_params


def test_close_account(stubbed_sender):
    """Test close account."""
    token_account = PublicKey(0)
    params = spl_token.CloseAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        dest=stubbed_sender.public_key,
        owner=stubbed_sender.public_key,
    )
    instruction = spl_token.close_account(params)
    assert spl_token.decode_close_account(instruction) == params

    multisig_params = spl_token.CloseAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        dest=stubbed_sender.public_key,
        owner=stubbed_sender.public_key,
        signers=[PublicKey(i + 1) for i in range(3)],
    )
    instruction = spl_token.close_account(multisig_params)
    assert spl_token.decode_close_account(instruction) == multisig_params


def test_freeze_account(stubbed_sender):
    """Test freeze account."""
    token_account, mint = PublicKey(0), PublicKey(1)
    params = spl_token.FreezeAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.public_key,
    )
    instruction = spl_token.freeze_account(params)
    assert spl_token.decode_freeze_account(instruction) == params

    multisig_params = spl_token.FreezeAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.public_key,
        multi_signers=[PublicKey(i) for i in range(2, 10)],
    )
    instruction = spl_token.freeze_account(multisig_params)
    assert spl_token.decode_freeze_account(instruction) == multisig_params


def test_thaw_account(stubbed_sender):
    """Test thaw account."""
    token_account, mint = PublicKey(0), PublicKey(1)
    params = spl_token.ThawAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.public_key,
    )
    instruction = spl_token.thaw_account(params)
    assert spl_token.decode_thaw_account(instruction) == params

    multisig_params = spl_token.ThawAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.public_key,
        multi_signers=[PublicKey(i) for i in range(2, 10)],
    )
    instruction = spl_token.thaw_account(multisig_params)
    assert spl_token.decode_thaw_account(instruction) == multisig_params


def test_transfer_checked(stubbed_receiver, stubbed_sender):
    """Test transfer_checked."""
    mint = PublicKey(0)
    params = spl_token.TransferCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key,
        mint=mint,
        dest=stubbed_receiver,
        owner=stubbed_sender.public_key,
        amount=123,
        decimals=6,
    )
    instruction = spl_token.transfer_checked(params)
    assert spl_token.decode_transfer_checked(instruction) == params

    multisig_params = spl_token.TransferCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key,
        mint=mint,
        dest=stubbed_receiver,
        owner=stubbed_sender.public_key,
        signers=[PublicKey(i + 1) for i in range(3)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.transfer_checked(multisig_params)
    assert spl_token.decode_transfer_checked(instruction) == multisig_params


def test_approve_checked(stubbed_receiver, stubbed_sender):
    """Test approve_checked."""
    mint = PublicKey(0)
    params = spl_token.ApproveCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key,
        mint=mint,
        delegate=stubbed_receiver,
        owner=stubbed_sender.public_key,
        amount=123,
        decimals=6,
    )
    instruction = spl_token.approve_checked(params)
    assert spl_token.decode_approve_checked(instruction) == params

    multisig_params = spl_token.ApproveCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.public_key,
        mint=mint,
        delegate=stubbed_receiver,
        owner=stubbed_sender.public_key,
        signers=[PublicKey(i + 1) for i in range(3)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.approve_checked(multisig_params)
    assert spl_token.decode_approve_checked(instruction) == multisig_params


def test_mint_to_checked(stubbed_receiver):
    """Test mint_to_checked."""
    mint, mint_authority = PublicKey(0), PublicKey(1)
    params = spl_token.MintToCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        dest=stubbed_receiver,
        mint_authority=mint_authority,
        amount=123,
        decimals=6,
    )
    instruction = spl_token.mint_to_checked(params)
    assert spl_token.decode_mint_to_checked(instruction) == params

    multisig_params = spl_token.MintToCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        dest=stubbed_receiver,
        mint_authority=mint_authority,
        signers=[PublicKey(i) for i in range(3, 10)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.mint_to_checked(multisig_params)
    assert spl_token.decode_mint_to_checked(instruction) == multisig_params


def test_burn_checked(stubbed_receiver):
    """Test burn_checked."""
    mint, owner = PublicKey(0), PublicKey(1)
    params = spl_token.BurnCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        account=stubbed_receiver,
        owner=owner,
        amount=123,
        decimals=6,
    )
    instruction = spl_token.burn_checked(params)
    assert spl_token.decode_burn_checked(instruction) == params

    multisig_params = spl_token.BurnCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint,
        account=stubbed_receiver,
        owner=owner,
        signers=[PublicKey(i) for i in range(3, 10)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.burn_checked(multisig_params)
    assert spl_token.decode_burn_checked(instruction) == multisig_params
