# ruff: noqa: PLR0913
"""Tests for SPL Token flows using AsyncClient + instruction composition."""

from __future__ import annotations

from typing import Any, Mapping, Sequence, cast

import pytest
import solders.system_program as sp
import spl.token._layouts as layouts
import spl.token.instructions as spl_token
import spl.token.models as spl_token_models
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.models import TokenAccountOpts, TxOpts
from spl.token.constants import (
    ACCOUNT_LEN,
    ASSOCIATED_TOKEN_PROGRAM_ID,
    MINT_LEN,
    MULTISIG_LEN,
    TOKEN_PROGRAM_ID,
)

from ..utils import AIRDROP_AMOUNT, OPTS, assert_valid_response


def _dedupe_signers(signers: Sequence[Keypair]) -> list[Keypair]:
    unique: dict[str, Keypair] = {}
    for signer in signers:
        unique[str(signer.pubkey())] = signer
    return list(unique.values())


async def _send_instructions(
    conn: AsyncClient,
    payer: Keypair,
    instructions: list[Instruction],
    signers: Sequence[Keypair] = (),
    opts: TxOpts = OPTS,
):
    recent_blockhash = (await conn.get_latest_blockhash()).value.blockhash
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=instructions,
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    tx_signers = _dedupe_signers([payer, *list(signers)])
    tx = VersionedTransaction(msg, tx_signers)
    resp = await conn.send_transaction(tx, opts=opts)
    assert_valid_response(resp)
    return resp


async def _send_and_confirm(
    conn: AsyncClient,
    payer: Keypair,
    instructions: list[Instruction],
    signers: Sequence[Keypair] = (),
    opts: TxOpts = OPTS,
):
    resp = await _send_instructions(conn, payer, instructions, signers=signers, opts=opts)
    await conn.confirm_transaction(resp.value)
    return resp


async def _get_account_data(conn: AsyncClient, account: Pubkey) -> bytes:
    resp = await conn.get_account_info(account)
    assert_valid_response(resp)
    assert resp.value is not None
    return resp.value.data


async def _get_token_balance_info(conn: AsyncClient, token_account: Pubkey):
    resp = await conn.get_token_account_balance(token_account)
    assert_valid_response(resp)
    return resp.value


async def _get_token_account_layout(conn: AsyncClient, token_account: Pubkey):
    return layouts.ACCOUNT_LAYOUT.parse(await _get_account_data(conn, token_account))


async def _create_mint(
    conn: AsyncClient,
    payer: Keypair,
    mint_authority: Pubkey,
    decimals: int,
    program_id: Pubkey,
    freeze_authority: Pubkey | None,
) -> Pubkey:
    mint_account = Keypair()
    rent_resp = await conn.get_minimum_balance_for_rent_exemption(MINT_LEN)
    assert_valid_response(rent_resp)

    create_ix = sp.create_account(
        sp.CreateAccountParams(
            from_pubkey=payer.pubkey(),
            to_pubkey=mint_account.pubkey(),
            lamports=rent_resp.value,
            space=MINT_LEN,
            owner=program_id,
        )
    )
    init_ix = spl_token.initialize_mint2(
        spl_token_models.InitializeMint2Params(
            decimals=decimals,
            program_id=program_id,
            mint=mint_account.pubkey(),
            mint_authority=mint_authority,
            freeze_authority=freeze_authority,
        )
    )
    await _send_instructions(conn, payer, [create_ix, init_ix], signers=[mint_account])
    return mint_account.pubkey()


async def _create_token_account(
    conn: AsyncClient,
    payer: Keypair,
    mint: Pubkey,
    owner: Pubkey,
    program_id: Pubkey,
) -> Pubkey:
    token_account = Keypair()
    rent_resp = await conn.get_minimum_balance_for_rent_exemption(ACCOUNT_LEN)
    assert_valid_response(rent_resp)

    create_ix = sp.create_account(
        sp.CreateAccountParams(
            from_pubkey=payer.pubkey(),
            to_pubkey=token_account.pubkey(),
            lamports=rent_resp.value,
            space=ACCOUNT_LEN,
            owner=program_id,
        )
    )
    init_ix = spl_token.initialize_account3(
        spl_token_models.InitializeAccount3Params(
            program_id=program_id,
            account=token_account.pubkey(),
            mint=mint,
            owner=owner,
        )
    )
    await _send_instructions(conn, payer, [create_ix, init_ix], signers=[token_account])
    return token_account.pubkey()


@pytest.fixture(scope="module")
async def test_token(
    async_stubbed_sender_for_token,
    freeze_authority,
    test_http_client_async: AsyncClient,
) -> Pubkey:
    """Create mint and return mint pubkey."""
    resp = await test_http_client_async.request_airdrop(async_stubbed_sender_for_token.pubkey(), AIRDROP_AMOUNT)
    await test_http_client_async.confirm_transaction(resp.value)
    assert_valid_response(resp)

    expected_decimals = 6
    mint = await _create_mint(
        conn=test_http_client_async,
        payer=async_stubbed_sender_for_token,
        mint_authority=async_stubbed_sender_for_token.pubkey(),
        decimals=expected_decimals,
        program_id=TOKEN_PROGRAM_ID,
        freeze_authority=freeze_authority.pubkey(),
    )

    resp = await test_http_client_async.get_account_info(mint)
    assert_valid_response(resp)
    assert resp.value is not None
    assert resp.value.owner == TOKEN_PROGRAM_ID

    mint_data = layouts.MINT_LAYOUT.parse(resp.value.data)
    assert mint_data.is_initialized
    assert mint_data.decimals == expected_decimals
    assert mint_data.supply == 0
    assert Pubkey(mint_data.mint_authority) == async_stubbed_sender_for_token.pubkey()
    assert Pubkey(mint_data.freeze_authority) == freeze_authority.pubkey()
    return mint


@pytest.fixture(scope="module")
async def stubbed_sender_token_account_pk(
    async_stubbed_sender_for_token,
    test_token,
    test_http_client_async: AsyncClient,
) -> Pubkey:
    """Token account for stubbed sender."""
    return await _create_token_account(
        conn=test_http_client_async,
        payer=async_stubbed_sender_for_token,
        mint=test_token,
        owner=async_stubbed_sender_for_token.pubkey(),
        program_id=TOKEN_PROGRAM_ID,
    )


@pytest.fixture(scope="module")
async def async_stubbed_receiver_token_account_pk(
    async_stubbed_sender_for_token,
    async_stubbed_receiver,
    test_token,
    test_http_client_async: AsyncClient,
) -> Pubkey:
    """Token account for stubbed receiver."""
    return await _create_token_account(
        conn=test_http_client_async,
        payer=async_stubbed_sender_for_token,
        mint=test_token,
        owner=async_stubbed_receiver,
        program_id=TOKEN_PROGRAM_ID,
    )


@pytest.mark.integration
async def test_new_account(
    async_stubbed_sender_for_token,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test creating a new token account."""
    token_account_pk = await _create_token_account(
        conn=test_http_client_async,
        payer=async_stubbed_sender_for_token,
        mint=test_token,
        owner=async_stubbed_sender_for_token.pubkey(),
        program_id=TOKEN_PROGRAM_ID,
    )
    resp = await test_http_client_async.get_account_info(token_account_pk)
    assert_valid_response(resp)
    assert resp.value is not None
    assert resp.value.owner == TOKEN_PROGRAM_ID

    account_data = layouts.ACCOUNT_LAYOUT.parse(resp.value.data)
    assert account_data.state
    assert not account_data.amount
    assert (
        not account_data.delegate_option
        and not account_data.delegated_amount
        and Pubkey(account_data.delegate) == Pubkey([0] * 31 + [0])
    )
    assert not account_data.close_authority_option and Pubkey(account_data.close_authority) == Pubkey([0] * 31 + [0])
    assert not account_data.is_native_option and not account_data.is_native
    assert Pubkey(account_data.mint) == test_token
    assert Pubkey(account_data.owner) == async_stubbed_sender_for_token.pubkey()


@pytest.mark.integration
async def test_new_associated_account(
    async_stubbed_sender_for_token,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test creating a new associated token account."""
    new_acct = Pubkey([0] * 31 + [0])
    create_ata_ix = spl_token.create_associated_token_account(
        async_stubbed_sender_for_token.pubkey(), new_acct, test_token, TOKEN_PROGRAM_ID
    )
    await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [create_ata_ix],
        opts=OPTS,
    )

    token_account_pubkey = spl_token.get_associated_token_address(new_acct, test_token, TOKEN_PROGRAM_ID)
    expected_token_account_key, _ = new_acct.find_program_address(
        seeds=[bytes(new_acct), bytes(TOKEN_PROGRAM_ID), bytes(test_token)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    assert token_account_pubkey == expected_token_account_key


@pytest.mark.integration
async def test_get_account_info(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test get token account info."""
    account_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    state = int(account_data.state)
    delegate = Pubkey(account_data.delegate) if account_data.delegate_option else None
    close_authority = Pubkey(account_data.close_authority) if account_data.close_authority_option else None
    rent_exempt_reserve = account_data.is_native if account_data.is_native_option else None

    account_info = spl_token_models.AccountInfo(
        mint=Pubkey(account_data.mint),
        owner=Pubkey(account_data.owner),
        amount=int(account_data.amount),
        delegate=delegate,
        delegated_amount=int(account_data.delegated_amount),
        is_initialized=state != 0,
        is_frozen=state == 2,
        is_native=bool(account_data.is_native_option),
        rent_exempt_reserve=rent_exempt_reserve,
        close_authority=close_authority,
    )

    assert account_info.is_initialized is True
    assert account_info.mint == test_token
    assert account_info.owner == async_stubbed_sender_for_token.pubkey()
    assert account_info.amount == 0
    assert account_info.delegate is None
    assert account_info.delegated_amount == 0
    assert account_info.is_frozen is False
    assert account_info.is_native is False
    assert account_info.rent_exempt_reserve is None
    assert account_info.close_authority is None


@pytest.mark.integration
async def test_get_mint_info(
    async_stubbed_sender_for_token,
    freeze_authority,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test get token mint info."""
    mint_data = layouts.MINT_LAYOUT.parse(await _get_account_data(test_http_client_async, test_token))
    mint_authority = Pubkey(mint_data.mint_authority) if mint_data.mint_authority_option else None
    freeze_auth = Pubkey(mint_data.freeze_authority) if mint_data.freeze_authority_option else None

    mint_info = spl_token_models.MintInfo(
        mint_authority=mint_authority,
        supply=int(mint_data.supply),
        decimals=int(mint_data.decimals),
        is_initialized=bool(mint_data.is_initialized),
        freeze_authority=freeze_auth,
    )

    assert mint_info.mint_authority == async_stubbed_sender_for_token.pubkey()
    assert mint_info.supply == 0
    assert mint_info.decimals == 6
    assert mint_info.is_initialized is True
    assert mint_info.freeze_authority == freeze_authority.pubkey()


@pytest.mark.integration
async def test_mint_to(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test mint token to account and get balance."""
    expected_amount = 1000
    mint_ix = spl_token.mint_to(
        spl_token_models.MintToParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=test_token,
            dest=stubbed_sender_token_account_pk,
            mint_authority=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount,
        )
    )
    resp = await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [mint_ix],
        signers=[async_stubbed_sender_for_token],
        opts=OPTS,
    )
    assert_valid_response(resp)

    balance_info = await _get_token_balance_info(test_http_client_async, stubbed_sender_token_account_pk)
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == 6
    assert balance_info.ui_amount == 0.001


@pytest.mark.integration
async def test_transfer(
    async_stubbed_sender_for_token,
    async_stubbed_receiver_token_account_pk,
    stubbed_sender_token_account_pk,
    test_http_client_async: AsyncClient,
):
    """Test token transfer."""
    expected_amount = 500
    transfer_ix = spl_token.transfer(
        spl_token_models.TransferParams(
            program_id=TOKEN_PROGRAM_ID,
            source=stubbed_sender_token_account_pk,
            dest=async_stubbed_receiver_token_account_pk,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount,
        )
    )
    resp = await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [transfer_ix],
        signers=[async_stubbed_sender_for_token],
        opts=OPTS,
    )
    assert_valid_response(resp)

    balance_info = await _get_token_balance_info(test_http_client_async, async_stubbed_receiver_token_account_pk)
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == 6
    assert balance_info.ui_amount == 0.0005


@pytest.mark.integration
async def test_burn(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test burning tokens."""
    burn_amount = 200
    expected_amount = 300

    burn_ix = spl_token.burn(
        spl_token_models.BurnParams(
            program_id=TOKEN_PROGRAM_ID,
            account=stubbed_sender_token_account_pk,
            mint=test_token,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=burn_amount,
        )
    )
    burn_resp = await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [burn_ix],
        signers=[async_stubbed_sender_for_token],
        opts=OPTS,
    )
    assert_valid_response(burn_resp)

    balance_info = await _get_token_balance_info(test_http_client_async, stubbed_sender_token_account_pk)
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == 6
    assert balance_info.ui_amount == 0.0003


@pytest.mark.integration
async def test_mint_to_checked(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test mint token checked and get balance."""
    expected_amount = 1000
    mint_amount = 700
    expected_decimals = 6

    mint_ix = spl_token.mint_to_checked(
        spl_token_models.MintToCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=test_token,
            dest=stubbed_sender_token_account_pk,
            mint_authority=async_stubbed_sender_for_token.pubkey(),
            amount=mint_amount,
            decimals=expected_decimals,
        )
    )
    mint_resp = await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [mint_ix],
        signers=[async_stubbed_sender_for_token],
        opts=OPTS,
    )
    assert_valid_response(mint_resp)

    balance_info = await _get_token_balance_info(test_http_client_async, stubbed_sender_token_account_pk)
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == expected_decimals
    assert balance_info.ui_amount == 0.001


@pytest.mark.integration
async def test_transfer_checked(
    async_stubbed_sender_for_token,
    async_stubbed_receiver_token_account_pk,
    stubbed_sender_token_account_pk,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test token transfer."""
    transfer_amount = 500
    total_amount = 1000
    expected_decimals = 6

    transfer_ix = spl_token.transfer_checked(
        spl_token_models.TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=stubbed_sender_token_account_pk,
            mint=test_token,
            dest=async_stubbed_receiver_token_account_pk,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=transfer_amount,
            decimals=expected_decimals,
        )
    )
    transfer_resp = await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [transfer_ix],
        signers=[async_stubbed_sender_for_token],
        opts=OPTS,
    )
    assert_valid_response(transfer_resp)

    balance_info = await _get_token_balance_info(test_http_client_async, async_stubbed_receiver_token_account_pk)
    assert balance_info.amount == str(total_amount)
    assert balance_info.decimals == expected_decimals
    assert balance_info.ui_amount == 0.001


@pytest.mark.integration
async def test_burn_checked(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    test_http_client_async: AsyncClient,
    test_token,
):
    """Test burning tokens checked."""
    burn_amount = 500
    expected_decimals = 6

    burn_ix = spl_token.burn_checked(
        spl_token_models.BurnCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            account=stubbed_sender_token_account_pk,
            mint=test_token,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=burn_amount,
            decimals=expected_decimals,
        )
    )
    burn_resp = await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [burn_ix],
        signers=[async_stubbed_sender_for_token],
        opts=OPTS,
    )
    assert_valid_response(burn_resp)

    balance_info = await _get_token_balance_info(test_http_client_async, stubbed_sender_token_account_pk)
    assert balance_info.amount == str(0)
    assert balance_info.decimals == expected_decimals
    assert balance_info.ui_amount == 0.0


@pytest.mark.integration
async def test_get_accounts(
    async_stubbed_sender_for_token,
    test_http_client_async: AsyncClient,
):
    """Test get token accounts."""
    resp = await test_http_client_async.get_token_accounts_by_owner_json_parsed(
        async_stubbed_sender_for_token.pubkey(),
        TokenAccountOpts(program_id=TOKEN_PROGRAM_ID),
    )
    assert_valid_response(resp)
    assert len(resp.value) == 2
    for resp_data in resp.value:
        assert resp_data.pubkey
        parsed = cast(Mapping[str, Any], resp_data.account.data.parsed)
        info = cast(Mapping[str, Any], parsed["info"])
        assert info["owner"] == str(async_stubbed_sender_for_token.pubkey())


@pytest.mark.integration
async def test_approve(
    async_stubbed_sender_for_token,
    async_stubbed_receiver,
    stubbed_sender_token_account_pk,
    test_http_client_async,
):
    """Test approval for delgating a token account."""
    expected_amount_delegated = 500
    approve_ix = spl_token.approve(
        spl_token_models.ApproveParams(
            program_id=TOKEN_PROGRAM_ID,
            source=stubbed_sender_token_account_pk,
            delegate=async_stubbed_receiver,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount_delegated,
        )
    )
    resp = await _send_and_confirm(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [approve_ix],
        opts=OPTS,
    )
    assert_valid_response(resp)

    account_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert Pubkey(account_data.delegate) == async_stubbed_receiver
    assert account_data.delegated_amount == expected_amount_delegated


@pytest.mark.integration
async def test_revoke(
    async_stubbed_sender_for_token,
    async_stubbed_receiver,
    stubbed_sender_token_account_pk,
    test_http_client_async,
):
    """Test revoke for undelgating a token account."""
    expected_amount_delegated = 500
    before_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert Pubkey(before_data.delegate) == async_stubbed_receiver
    assert before_data.delegated_amount == expected_amount_delegated

    revoke_ix = spl_token.revoke(
        spl_token_models.RevokeParams(
            program_id=TOKEN_PROGRAM_ID,
            account=stubbed_sender_token_account_pk,
            owner=async_stubbed_sender_for_token.pubkey(),
        )
    )
    revoke_resp = await _send_and_confirm(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [revoke_ix],
        opts=OPTS,
    )
    assert_valid_response(revoke_resp)

    after_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert after_data.delegate_option == 0
    assert after_data.delegated_amount == 0


@pytest.mark.integration
async def test_approve_checked(
    async_stubbed_sender_for_token,
    async_stubbed_receiver,
    stubbed_sender_token_account_pk,
    test_http_client_async,
    test_token,
):
    """Test approve_checked for delegating a token account."""
    expected_amount_delegated = 500
    approve_ix = spl_token.approve_checked(
        spl_token_models.ApproveCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=stubbed_sender_token_account_pk,
            mint=test_token,
            delegate=async_stubbed_receiver,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount_delegated,
            decimals=6,
        )
    )
    resp = await _send_and_confirm(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [approve_ix],
        opts=OPTS,
    )
    assert_valid_response(resp)

    account_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert Pubkey(account_data.delegate) == async_stubbed_receiver
    assert account_data.delegated_amount == expected_amount_delegated


@pytest.mark.integration
async def test_freeze_account(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    freeze_authority,
    test_http_client_async,
    test_token,
):
    """Test freezing an account."""
    resp = await test_http_client_async.request_airdrop(freeze_authority.pubkey(), AIRDROP_AMOUNT)
    await test_http_client_async.confirm_transaction(resp.value)
    assert_valid_response(resp)

    before_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert int(before_data.state) != 2

    freeze_ix = spl_token.freeze_account(
        spl_token_models.FreezeAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=stubbed_sender_token_account_pk,
            mint=test_token,
            authority=freeze_authority.pubkey(),
        )
    )
    freeze_resp = await _send_and_confirm(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [freeze_ix],
        signers=[freeze_authority],
        opts=OPTS,
    )
    assert_valid_response(freeze_resp)

    after_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert int(after_data.state) == 2


@pytest.mark.integration
async def test_thaw_account(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    freeze_authority,
    test_http_client_async,
    test_token,
):
    """Test thawing an account."""
    before_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert int(before_data.state) == 2

    thaw_ix = spl_token.thaw_account(
        spl_token_models.ThawAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=stubbed_sender_token_account_pk,
            mint=test_token,
            authority=freeze_authority.pubkey(),
        )
    )
    thaw_resp = await _send_and_confirm(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [thaw_ix],
        signers=[freeze_authority],
        opts=OPTS,
    )
    assert_valid_response(thaw_resp)

    after_data = await _get_token_account_layout(test_http_client_async, stubbed_sender_token_account_pk)
    assert int(after_data.state) != 2


@pytest.mark.integration
async def test_close_account(
    async_stubbed_sender_for_token,
    stubbed_sender_token_account_pk,
    async_stubbed_receiver_token_account_pk,
    test_http_client_async,
):
    """Test closing a token account."""
    create_resp = await test_http_client_async.get_account_info(stubbed_sender_token_account_pk)
    assert_valid_response(create_resp)
    assert create_resp.value is not None
    assert create_resp.value.data

    close_ix = spl_token.close_account(
        spl_token_models.CloseAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=stubbed_sender_token_account_pk,
            dest=async_stubbed_receiver_token_account_pk,
            owner=async_stubbed_sender_for_token.pubkey(),
        )
    )
    close_resp = await _send_and_confirm(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [close_ix],
        signers=[async_stubbed_sender_for_token],
        opts=OPTS,
    )
    assert_valid_response(close_resp)

    info_resp = await test_http_client_async.get_account_info(stubbed_sender_token_account_pk)
    assert_valid_response(info_resp)
    assert info_resp.value is None


@pytest.mark.integration
async def test_create_multisig(
    async_stubbed_sender_for_token,
    async_stubbed_receiver,
    test_http_client_async: AsyncClient,
):
    """Test creating a multisig account."""
    min_signers = 2
    multisig_account = Keypair()
    rent_resp = await test_http_client_async.get_minimum_balance_for_rent_exemption(MULTISIG_LEN)
    assert_valid_response(rent_resp)

    create_ix = sp.create_account(
        sp.CreateAccountParams(
            from_pubkey=async_stubbed_sender_for_token.pubkey(),
            to_pubkey=multisig_account.pubkey(),
            lamports=rent_resp.value,
            space=MULTISIG_LEN,
            owner=TOKEN_PROGRAM_ID,
        )
    )
    init_ix = spl_token.initialize_multisig2(
        spl_token_models.InitializeMultisig2Params(
            program_id=TOKEN_PROGRAM_ID,
            multisig=multisig_account.pubkey(),
            m=min_signers,
            signers=[async_stubbed_sender_for_token.pubkey(), async_stubbed_receiver],
        )
    )
    await _send_instructions(
        test_http_client_async,
        async_stubbed_sender_for_token,
        [create_ix, init_ix],
        signers=[multisig_account],
        opts=OPTS,
    )

    resp = await test_http_client_async.get_account_info(multisig_account.pubkey())
    assert_valid_response(resp)
    assert resp.value is not None
    assert resp.value.owner == TOKEN_PROGRAM_ID

    multisig_data = layouts.MULTISIG_LAYOUT.parse(resp.value.data)
    assert multisig_data.is_initialized
    assert multisig_data.m == min_signers
    assert Pubkey(multisig_data.signer1) == async_stubbed_sender_for_token.pubkey()
    assert Pubkey(multisig_data.signer2) == async_stubbed_receiver
