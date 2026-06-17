"""Unit tests for SPL-token instructions."""

import spl.token.instructions as spl_token
from solders.pubkey import Pubkey
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from spl.token.constants import (
    TOKEN_PROGRAM_ID,
    TOKEN_2022_PROGRAM_ID,
    WRAPPED_SOL_MINT,
    ASSOCIATED_TOKEN_PROGRAM_ID,
)
from spl.token.instructions import get_associated_token_address


def test_initialize_mint(stubbed_sender):
    """Test initialize mint."""
    mint_authority, freeze_authority = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
    params_with_freeze = spl_token.InitializeMintParams(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.pubkey(),
        mint_authority=mint_authority,
        freeze_authority=freeze_authority,
    )
    instruction = spl_token.initialize_mint(params_with_freeze)
    assert spl_token.decode_initialize_mint(instruction) == params_with_freeze

    params_no_freeze = spl_token.InitializeMintParams(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.pubkey(),
        mint_authority=mint_authority,
    )
    instruction = spl_token.initialize_mint(params_no_freeze)
    decoded_params = spl_token.decode_initialize_mint(instruction)
    assert not decoded_params.freeze_authority
    assert decoded_params == params_no_freeze


def test_initialize_mint2(stubbed_sender):
    """Test initialize mint2."""
    mint_authority, freeze_authority = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
    params_with_freeze = spl_token.InitializeMint2Params(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.pubkey(),
        mint_authority=mint_authority,
        freeze_authority=freeze_authority,
    )
    instruction = spl_token.initialize_mint2(params_with_freeze)
    assert spl_token.decode_initialize_mint2(instruction) == params_with_freeze

    params_no_freeze = spl_token.InitializeMint2Params(
        decimals=18,
        program_id=TOKEN_PROGRAM_ID,
        mint=stubbed_sender.pubkey(),
        mint_authority=mint_authority,
    )
    instruction = spl_token.initialize_mint2(params_no_freeze)
    decoded_params = spl_token.decode_initialize_mint2(instruction)
    assert not decoded_params.freeze_authority
    assert decoded_params == params_no_freeze


def test_initialize_account(stubbed_sender):
    """Test initialize account."""
    new_account, token_mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
    params = spl_token.InitializeAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=new_account,
        mint=token_mint,
        owner=stubbed_sender.pubkey(),
    )
    instruction = spl_token.initialize_account(params)
    assert spl_token.decode_initialize_account(instruction) == params


def test_initialize_account2(stubbed_sender):
    """Test initialize account2."""
    new_account, token_mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
    params = spl_token.InitializeAccount2Params(
        program_id=TOKEN_PROGRAM_ID,
        account=new_account,
        mint=token_mint,
        owner=stubbed_sender.pubkey(),
    )
    instruction = spl_token.initialize_account2(params)
    assert spl_token.decode_initialize_account2(instruction) == params


def test_initialize_account3(stubbed_sender):
    """Test initialize account3."""
    new_account, token_mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
    params = spl_token.InitializeAccount3Params(
        program_id=TOKEN_PROGRAM_ID,
        account=new_account,
        mint=token_mint,
        owner=stubbed_sender.pubkey(),
    )
    instruction = spl_token.initialize_account3(params)
    assert spl_token.decode_initialize_account3(instruction) == params


def test_initialize_multisig():
    """Test initialize multisig."""
    new_multisig = Pubkey([0] * 31 + [0])
    signers = [Pubkey([0] * 31 + [i + 1]) for i in range(3)]
    params = spl_token.InitializeMultisigParams(
        program_id=TOKEN_PROGRAM_ID,
        multisig=new_multisig,
        signers=signers,
        m=len(signers),
    )
    instruction = spl_token.initialize_multisig(params)
    assert spl_token.decode_initialize_multisig(instruction) == params


def test_initialize_multisig2():
    """Test initialize multisig2."""
    new_multisig = Pubkey([0] * 31 + [0])
    signers = [Pubkey([0] * 31 + [i + 1]) for i in range(3)]
    params = spl_token.InitializeMultisig2Params(
        program_id=TOKEN_PROGRAM_ID,
        multisig=new_multisig,
        signers=signers,
        m=len(signers),
    )
    instruction = spl_token.initialize_multisig2(params)
    assert spl_token.decode_initialize_multisig2(instruction) == params


def test_transfer(stubbed_receiver, stubbed_sender):
    """Test transfer."""
    params = spl_token.TransferParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        dest=stubbed_receiver,
        owner=stubbed_sender.pubkey(),
        amount=123,
    )
    instruction = spl_token.transfer(params)
    assert spl_token.decode_transfer(instruction) == params

    multisig_params = spl_token.TransferParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        dest=stubbed_receiver,
        owner=stubbed_sender.pubkey(),
        signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
        amount=123,
    )
    instruction = spl_token.transfer(multisig_params)
    assert spl_token.decode_transfer(instruction) == multisig_params


def test_approve(stubbed_sender):
    """Test approve."""
    delegate_account = Pubkey([0] * 31 + [0])
    params = spl_token.ApproveParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        delegate=delegate_account,
        owner=stubbed_sender.pubkey(),
        amount=123,
    )
    instruction = spl_token.approve(params)
    assert spl_token.decode_approve(instruction) == params

    multisig_params = spl_token.ApproveParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        delegate=delegate_account,
        owner=stubbed_sender.pubkey(),
        signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
        amount=123,
    )
    instruction = spl_token.approve(multisig_params)
    assert spl_token.decode_approve(instruction) == multisig_params


def test_revoke(stubbed_sender):
    """Test revoke."""
    delegate_account = Pubkey([0] * 31 + [0])
    params = spl_token.RevokeParams(
        program_id=TOKEN_PROGRAM_ID,
        account=delegate_account,
        owner=stubbed_sender.pubkey(),
    )
    instruction = spl_token.revoke(params)
    assert spl_token.decode_revoke(instruction) == params

    multisig_params = spl_token.RevokeParams(
        program_id=TOKEN_PROGRAM_ID,
        account=delegate_account,
        owner=stubbed_sender.pubkey(),
        signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
    )
    instruction = spl_token.revoke(multisig_params)
    assert spl_token.decode_revoke(instruction) == multisig_params


def test_set_authority():
    """Test set authority."""
    account, new_authority, current_authority = (
        Pubkey([0] * 31 + [0]),
        Pubkey([0] * 31 + [1]),
        Pubkey([0] * 31 + [2]),
    )
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
        signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
    )
    instruction = spl_token.set_authority(multisig_params)
    decoded_params = spl_token.decode_set_authority(instruction)
    assert not decoded_params.new_authority
    assert decoded_params == multisig_params


def test_mint_to(stubbed_receiver):
    """Test mint to."""
    mint, mint_authority = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
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
        signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
        amount=123,
    )
    instruction = spl_token.mint_to(multisig_params)
    assert spl_token.decode_mint_to(instruction) == multisig_params


def test_burn(stubbed_receiver):
    """Test burn."""
    mint, owner = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
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
        signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
        amount=123,
    )
    instruction = spl_token.burn(multisig_params)
    assert spl_token.decode_burn(instruction) == multisig_params


def test_close_account(stubbed_sender):
    """Test close account."""
    token_account = Pubkey([0] * 31 + [0])
    params = spl_token.CloseAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        dest=stubbed_sender.pubkey(),
        owner=stubbed_sender.pubkey(),
    )
    instruction = spl_token.close_account(params)
    assert spl_token.decode_close_account(instruction) == params

    multisig_params = spl_token.CloseAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        dest=stubbed_sender.pubkey(),
        owner=stubbed_sender.pubkey(),
        signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
    )
    instruction = spl_token.close_account(multisig_params)
    assert spl_token.decode_close_account(instruction) == multisig_params


def test_freeze_account(stubbed_sender):
    """Test freeze account."""
    token_account, mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
    params = spl_token.FreezeAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.pubkey(),
    )
    instruction = spl_token.freeze_account(params)
    assert spl_token.decode_freeze_account(instruction) == params

    multisig_params = spl_token.FreezeAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.pubkey(),
        multi_signers=[Pubkey([0] * 31 + [i]) for i in range(2, 10)],
    )
    instruction = spl_token.freeze_account(multisig_params)
    assert spl_token.decode_freeze_account(instruction) == multisig_params


def test_thaw_account(stubbed_sender):
    """Test thaw account."""
    token_account, mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
    params = spl_token.ThawAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.pubkey(),
    )
    instruction = spl_token.thaw_account(params)
    assert spl_token.decode_thaw_account(instruction) == params

    multisig_params = spl_token.ThawAccountParams(
        program_id=TOKEN_PROGRAM_ID,
        account=token_account,
        mint=mint,
        authority=stubbed_sender.pubkey(),
        multi_signers=[Pubkey([0] * 31 + [i]) for i in range(2, 10)],
    )
    instruction = spl_token.thaw_account(multisig_params)
    assert spl_token.decode_thaw_account(instruction) == multisig_params


def test_transfer_checked(stubbed_receiver, stubbed_sender):
    """Test transfer_checked."""
    mint = Pubkey([0] * 31 + [0])
    params = spl_token.TransferCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        mint=mint,
        dest=stubbed_receiver,
        owner=stubbed_sender.pubkey(),
        amount=123,
        decimals=6,
    )
    instruction = spl_token.transfer_checked(params)
    assert spl_token.decode_transfer_checked(instruction) == params

    multisig_params = spl_token.TransferCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        mint=mint,
        dest=stubbed_receiver,
        owner=stubbed_sender.pubkey(),
        signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.transfer_checked(multisig_params)
    assert spl_token.decode_transfer_checked(instruction) == multisig_params


def test_approve_checked(stubbed_receiver, stubbed_sender):
    """Test approve_checked."""
    mint = Pubkey([0] * 31 + [0])
    params = spl_token.ApproveCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        mint=mint,
        delegate=stubbed_receiver,
        owner=stubbed_sender.pubkey(),
        amount=123,
        decimals=6,
    )
    instruction = spl_token.approve_checked(params)
    assert spl_token.decode_approve_checked(instruction) == params

    multisig_params = spl_token.ApproveCheckedParams(
        program_id=TOKEN_PROGRAM_ID,
        source=stubbed_sender.pubkey(),
        mint=mint,
        delegate=stubbed_receiver,
        owner=stubbed_sender.pubkey(),
        signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.approve_checked(multisig_params)
    assert spl_token.decode_approve_checked(instruction) == multisig_params


def test_mint_to_checked(stubbed_receiver):
    """Test mint_to_checked."""
    mint, mint_authority = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
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
        signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.mint_to_checked(multisig_params)
    assert spl_token.decode_mint_to_checked(instruction) == multisig_params


def test_burn_checked(stubbed_receiver):
    """Test burn_checked."""
    mint, owner = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
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
        signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
        amount=123,
        decimals=6,
    )
    instruction = spl_token.burn_checked(multisig_params)
    assert spl_token.decode_burn_checked(instruction) == multisig_params


def test_sync_native(stubbed_sender):
    """Test sync account amount value with lamports."""
    token_account = get_associated_token_address(
        stubbed_sender.pubkey(), WRAPPED_SOL_MINT
    )
    params = spl_token.SyncNativeParams(
        program_id=TOKEN_PROGRAM_ID, account=token_account
    )

    instruction = spl_token.sync_native(params)
    decoded_params = spl_token.decode_sync_native(instruction)
    assert params == decoded_params


def test_get_account_data_size():
    """Test get_account_data_size."""
    mint = Pubkey([0] * 31 + [0])
    params = spl_token.GetAccountDataSizeParams(program_id=TOKEN_PROGRAM_ID, mint=mint)
    instruction = spl_token.get_account_data_size(params)
    assert spl_token.decode_get_account_data_size(instruction) == params


def test_initialize_immutable_owner():
    """Test initialize_immutable_owner."""
    account = Pubkey([0] * 31 + [0])
    params = spl_token.InitializeImmutableOwnerParams(
        program_id=TOKEN_PROGRAM_ID, account=account
    )
    instruction = spl_token.initialize_immutable_owner(params)
    assert spl_token.decode_initialize_immutable_owner(instruction) == params


def test_initialize_transfer_fee_config():
    """Test initialize_transfer_fee_config."""
    mint = Pubkey([0] * 31 + [0])
    transfer_fee_config_authority = Pubkey([11] * 32)
    params = spl_token.InitializeTransferFeeConfigParams(
        program_id=TOKEN_2022_PROGRAM_ID,
        mint=mint,
        transfer_fee_config_authority=transfer_fee_config_authority,
        withdraw_withheld_authority=None,
        transfer_fee_basis_points=111,
        maximum_fee=2**64 - 1,
    )
    instruction = spl_token.initialize_transfer_fee_config(params)

    expected_data = bytes([26, 0, 1])
    expected_data += bytes(transfer_fee_config_authority)
    expected_data += bytes([0, 111, 0])
    expected_data += (2**64 - 1).to_bytes(8, "little")

    assert instruction.program_id == TOKEN_2022_PROGRAM_ID
    assert instruction.data == expected_data
    assert len(instruction.accounts) == 1
    assert instruction.accounts[0].pubkey == mint
    assert not instruction.accounts[0].is_signer
    assert instruction.accounts[0].is_writable
    assert spl_token.decode_initialize_transfer_fee_config(instruction) == params

    params_no_authorities = spl_token.InitializeTransferFeeConfigParams(
        program_id=TOKEN_2022_PROGRAM_ID,
        mint=mint,
        transfer_fee_config_authority=None,
        withdraw_withheld_authority=None,
        transfer_fee_basis_points=25,
        maximum_fee=10_000,
    )
    instruction = spl_token.initialize_transfer_fee_config(params_no_authorities)

    assert instruction.data == bytes([26, 0, 0, 0, 25, 0]) + (10_000).to_bytes(
        8, "little"
    )
    assert (
        spl_token.decode_initialize_transfer_fee_config(instruction)
        == params_no_authorities
    )


def test_withdraw_withheld_tokens_from_accounts():
    """Test withdraw_withheld_tokens_from_accounts."""
    mint = Pubkey([0] * 31 + [0])
    dest = Pubkey([0] * 31 + [1])
    authority = Pubkey([0] * 31 + [2])
    sources = [Pubkey([0] * 31 + [i]) for i in range(3, 6)]
    params = spl_token.WithdrawWithheldTokensFromAccountsParams(
        program_id=TOKEN_2022_PROGRAM_ID,
        mint=mint,
        dest=dest,
        authority=authority,
        sources=sources,
    )
    instruction = spl_token.withdraw_withheld_tokens_from_accounts(params)

    assert instruction.program_id == TOKEN_2022_PROGRAM_ID
    assert instruction.data == bytes([26, 3, len(sources)])
    assert (
        spl_token.decode_withdraw_withheld_tokens_from_accounts(instruction) == params
    )
    assert len(instruction.accounts) == 3 + len(sources)
    assert instruction.accounts[0].pubkey == mint
    assert not instruction.accounts[0].is_signer
    assert not instruction.accounts[0].is_writable
    assert instruction.accounts[1].pubkey == dest
    assert not instruction.accounts[1].is_signer
    assert instruction.accounts[1].is_writable
    assert instruction.accounts[2].pubkey == authority
    assert instruction.accounts[2].is_signer
    assert not instruction.accounts[2].is_writable
    for account, source in zip(instruction.accounts[3:], sources, strict=False):
        assert account.pubkey == source
        assert not account.is_signer
        assert account.is_writable

    signers = [Pubkey([0] * 31 + [i]) for i in range(6, 9)]
    multisig_params = spl_token.WithdrawWithheldTokensFromAccountsParams(
        program_id=TOKEN_2022_PROGRAM_ID,
        mint=mint,
        dest=dest,
        authority=authority,
        signers=signers,
        sources=sources,
    )
    instruction = spl_token.withdraw_withheld_tokens_from_accounts(multisig_params)

    assert instruction.data == bytes([26, 3, len(sources)])
    assert (
        spl_token.decode_withdraw_withheld_tokens_from_accounts(instruction)
        == multisig_params
    )
    assert len(instruction.accounts) == 3 + len(signers) + len(sources)
    assert instruction.accounts[2].pubkey == authority
    assert not instruction.accounts[2].is_signer
    assert not instruction.accounts[2].is_writable
    for account, signer in zip(
        instruction.accounts[3 : 3 + len(signers)], signers, strict=False
    ):
        assert account.pubkey == signer
        assert account.is_signer
        assert not account.is_writable
    for account, source in zip(
        instruction.accounts[3 + len(signers) :], sources, strict=False
    ):
        assert account.pubkey == source
        assert not account.is_signer
        assert account.is_writable


def test_withdraw_withheld_tokens_from_mint():
    """Test withdraw_withheld_tokens_from_mint."""
    mint = Pubkey([0] * 31 + [0])
    dest = Pubkey([0] * 31 + [1])
    authority = Pubkey([0] * 31 + [2])
    params = spl_token.WithdrawWithheldTokensFromMintParams(
        program_id=TOKEN_2022_PROGRAM_ID,
        mint=mint,
        dest=dest,
        authority=authority,
    )
    instruction = spl_token.withdraw_withheld_tokens_from_mint(params)

    assert instruction.program_id == TOKEN_2022_PROGRAM_ID
    assert instruction.data == bytes([26, 2])
    assert spl_token.decode_withdraw_withheld_tokens_from_mint(instruction) == params
    assert len(instruction.accounts) == 3
    assert instruction.accounts[0].pubkey == mint
    assert not instruction.accounts[0].is_signer
    assert instruction.accounts[0].is_writable
    assert instruction.accounts[1].pubkey == dest
    assert not instruction.accounts[1].is_signer
    assert instruction.accounts[1].is_writable
    assert instruction.accounts[2].pubkey == authority
    assert instruction.accounts[2].is_signer
    assert not instruction.accounts[2].is_writable

    signers = [Pubkey([0] * 31 + [i]) for i in range(3, 6)]
    multisig_params = spl_token.WithdrawWithheldTokensFromMintParams(
        program_id=TOKEN_2022_PROGRAM_ID,
        mint=mint,
        dest=dest,
        authority=authority,
        signers=signers,
    )
    instruction = spl_token.withdraw_withheld_tokens_from_mint(multisig_params)

    assert instruction.data == bytes([26, 2])
    assert (
        spl_token.decode_withdraw_withheld_tokens_from_mint(instruction)
        == multisig_params
    )
    assert len(instruction.accounts) == 3 + len(signers)
    assert instruction.accounts[2].pubkey == authority
    assert not instruction.accounts[2].is_signer
    assert not instruction.accounts[2].is_writable
    for account, signer in zip(instruction.accounts[3:], signers, strict=False):
        assert account.pubkey == signer
        assert account.is_signer
        assert not account.is_writable


def test_harvest_withheld_tokens_to_mint():
    """Test harvest_withheld_tokens_to_mint."""
    mint = Pubkey([0] * 31 + [0])
    sources = [Pubkey([0] * 31 + [i]) for i in range(1, 4)]
    params = spl_token.HarvestWithheldTokensToMintParams(
        program_id=TOKEN_2022_PROGRAM_ID,
        mint=mint,
        sources=sources,
    )
    instruction = spl_token.harvest_withheld_tokens_to_mint(params)

    assert instruction.program_id == TOKEN_2022_PROGRAM_ID
    assert instruction.data == bytes([26, 4])
    assert spl_token.decode_harvest_withheld_tokens_to_mint(instruction) == params
    assert len(instruction.accounts) == 1 + len(sources)
    assert instruction.accounts[0].pubkey == mint
    assert not instruction.accounts[0].is_signer
    assert instruction.accounts[0].is_writable
    for account, source in zip(instruction.accounts[1:], sources, strict=False):
        assert account.pubkey == source
        assert not account.is_signer
        assert account.is_writable


def test_amount_to_ui_amount():
    """Test amount_to_ui_amount."""
    mint = Pubkey([0] * 31 + [0])
    params = spl_token.AmountToUiAmountParams(
        program_id=TOKEN_PROGRAM_ID, mint=mint, amount=42
    )
    instruction = spl_token.amount_to_ui_amount(params)
    assert spl_token.decode_amount_to_ui_amount(instruction) == params


def test_ui_amount_to_amount():
    """Test ui_amount_to_amount."""
    mint = Pubkey([0] * 31 + [0])
    params = spl_token.UiAmountToAmountParams(
        program_id=TOKEN_PROGRAM_ID, mint=mint, ui_amount="0.42"
    )
    instruction = spl_token.ui_amount_to_amount(params)
    assert spl_token.decode_ui_amount_to_amount(instruction) == params


def test_get_associated_token_address_uses_expected_seed_order():
    """Test associated token address derivation seed order."""
    owner = Pubkey.new_unique()
    mint = Pubkey.new_unique()
    expected, _ = Pubkey.find_program_address(
        seeds=[bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )

    actual = get_associated_token_address(
        owner=owner, mint=mint, token_program_id=TOKEN_PROGRAM_ID
    )

    assert actual == expected


def test_create_idempotent_token_account(stubbed_receiver, stubbed_sender):
    """Test Create idempotent token account."""
    mint = Pubkey([0] * 31 + [0])
    token_account = get_associated_token_address(stubbed_receiver, mint)
    instruction = spl_token.create_idempotent_associated_token_account(
        payer=stubbed_sender.pubkey(),
        owner=stubbed_receiver,
        mint=mint,
    )

    assert instruction.program_id == ASSOCIATED_TOKEN_PROGRAM_ID
    assert instruction.data[0] == 1  # CreateIdempotent
    assert len(instruction.accounts) == 6
    assert instruction.accounts[0].pubkey == stubbed_sender.pubkey()
    assert instruction.accounts[0].is_signer
    assert instruction.accounts[0].is_writable
    assert instruction.accounts[1].pubkey == token_account
    assert not instruction.accounts[1].is_signer
    assert instruction.accounts[1].is_writable
    assert instruction.accounts[2].pubkey == stubbed_receiver
    assert not instruction.accounts[2].is_signer
    assert not instruction.accounts[2].is_writable
    assert instruction.accounts[3].pubkey == mint
    assert not instruction.accounts[3].is_signer
    assert not instruction.accounts[3].is_writable
    assert instruction.accounts[4].pubkey == SYSTEM_PROGRAM_ID
    assert not instruction.accounts[4].is_signer
    assert not instruction.accounts[4].is_writable
    assert instruction.accounts[5].pubkey == TOKEN_PROGRAM_ID
    assert not instruction.accounts[5].is_signer
    assert not instruction.accounts[5].is_writable
