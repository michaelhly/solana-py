# pylint: disable=R0401,redefined-outer-name
"""Integration tests for SPL Token operations using AsyncClient and spl.token.instructions."""

import pytest
import spl.token._layouts as layouts
import spl.token.instructions as spl_token
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.system_program import create_account
from solders.system_program import CreateAccountParams
from solders.transaction import VersionedTransaction
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

from solana.rpc.async_api import AsyncClient
from solana.rpc.models import TokenAccountOpts

from ..utils import AIRDROP_AMOUNT, OPTS, assert_valid_response

# ── helpers ──────────────────────────────────────────────────────────


async def _create_mint(
    client: AsyncClient,
    payer: Keypair,
    mint_authority: Pubkey,
    decimals: int,
    program_id: Pubkey,
    freeze_authority: Pubkey | None = None,
) -> Pubkey:
    """Create and initialize a new token mint. Returns the mint pubkey."""
    mint_keypair = Keypair()
    space = layouts.MINT_LAYOUT.sizeof()
    balance_needed = (await client.get_minimum_balance_for_rent_exemption(space)).value
    blockhash = (await client.get_latest_blockhash()).value.blockhash

    ixs = [
        create_account(
            CreateAccountParams(
                from_pubkey=payer.pubkey(),
                to_pubkey=mint_keypair.pubkey(),
                lamports=balance_needed,
                space=space,
                owner=program_id,
            )
        ),
        spl_token.initialize_mint(
            spl_token.models.InitializeMintParams(
                decimals=decimals,
                program_id=program_id,
                mint=mint_keypair.pubkey(),
                mint_authority=mint_authority,
                freeze_authority=freeze_authority,
            )
        ),
    ]
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [payer, mint_keypair])
    resp = await client.send_transaction(txn, opts=OPTS)
    await client.confirm_transaction(resp.value)
    return mint_keypair.pubkey()


async def _create_token_account(
    client: AsyncClient,
    payer: Keypair,
    owner: Pubkey,
    mint: Pubkey,
    program_id: Pubkey = TOKEN_PROGRAM_ID,
) -> Pubkey:
    """Create and initialize a new token account. Returns the account pubkey."""
    new_keypair = Keypair()
    space = layouts.ACCOUNT_LAYOUT.sizeof()
    balance_needed = (await client.get_minimum_balance_for_rent_exemption(space)).value
    blockhash = (await client.get_latest_blockhash()).value.blockhash

    ixs = [
        create_account(
            CreateAccountParams(
                from_pubkey=payer.pubkey(),
                to_pubkey=new_keypair.pubkey(),
                lamports=balance_needed,
                space=space,
                owner=program_id,
            )
        ),
        spl_token.initialize_account(
            spl_token.models.InitializeAccountParams(
                program_id=program_id,
                account=new_keypair.pubkey(),
                mint=mint,
                owner=owner,
            )
        ),
    ]
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [payer, new_keypair])
    resp = await client.send_transaction(txn, opts=OPTS)
    await client.confirm_transaction(resp.value)
    return new_keypair.pubkey()


# ── fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
async def test_mint(
    async_stubbed_sender_for_token: Keypair,
    freeze_authority: Keypair,
    test_http_client_async: AsyncClient,
) -> Pubkey:
    """Create a test mint and fund the payer."""
    client = test_http_client_async
    resp = await client.request_airdrop(
        async_stubbed_sender_for_token.pubkey(), AIRDROP_AMOUNT
    )
    await client.confirm_transaction(resp.value)
    balance = await client.get_balance(async_stubbed_sender_for_token.pubkey())
    assert balance.value == AIRDROP_AMOUNT

    expected_decimals = 6
    mint_pubkey = await _create_mint(
        client,
        async_stubbed_sender_for_token,
        async_stubbed_sender_for_token.pubkey(),
        expected_decimals,
        TOKEN_PROGRAM_ID,
        freeze_authority.pubkey(),
    )
    resp = await client.get_account_info(mint_pubkey)
    assert_valid_response(resp)
    assert resp.value.owner == TOKEN_PROGRAM_ID

    mint_data = layouts.MINT_LAYOUT.parse(resp.value.data)
    assert mint_data.is_initialized
    assert mint_data.decimals == expected_decimals
    assert mint_data.supply == 0
    assert Pubkey(mint_data.mint_authority) == async_stubbed_sender_for_token.pubkey()
    assert Pubkey(mint_data.freeze_authority) == freeze_authority.pubkey()
    return mint_pubkey


@pytest.fixture(scope="module")
async def sender_token_account(
    async_stubbed_sender_for_token: Keypair,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
) -> Pubkey:
    """Token account for stubbed sender."""
    return await _create_token_account(
        test_http_client_async,
        async_stubbed_sender_for_token,
        async_stubbed_sender_for_token.pubkey(),
        test_mint,
    )


@pytest.fixture(scope="module")
async def receiver_token_account(
    async_stubbed_receiver: Pubkey,
    async_stubbed_sender_for_token: Keypair,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
) -> Pubkey:
    """Token account for stubbed receiver."""
    return await _create_token_account(
        test_http_client_async,
        async_stubbed_sender_for_token,
        async_stubbed_receiver,
        test_mint,
    )


# ── tests ────────────────────────────────────────────────────────────


@pytest.mark.integration
async def test_new_account(
    async_stubbed_sender_for_token: Keypair,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test creating a new token account."""
    token_account_pk = await _create_token_account(
        test_http_client_async,
        async_stubbed_sender_for_token,
        async_stubbed_sender_for_token.pubkey(),
        test_mint,
    )
    resp = await test_http_client_async.get_account_info(token_account_pk)
    assert_valid_response(resp)
    assert resp.value.owner == TOKEN_PROGRAM_ID

    account_data = layouts.ACCOUNT_LAYOUT.parse(resp.value.data)
    assert account_data.state
    assert not account_data.amount
    assert (
        not account_data.delegate_option
        and not account_data.delegated_amount
        and Pubkey(account_data.delegate) == Pubkey([0] * 31 + [0])
    )
    assert not account_data.close_authority_option and Pubkey(
        account_data.close_authority
    ) == Pubkey([0] * 31 + [0])
    assert not account_data.is_native_option and not account_data.is_native
    assert Pubkey(account_data.mint) == test_mint
    assert Pubkey(account_data.owner) == async_stubbed_sender_for_token.pubkey()


@pytest.mark.integration
async def test_new_associated_account(test_mint: Pubkey):
    """Test creating a new associated token account."""
    new_acct = Pubkey([0] * 31 + [0])
    expected_token_account_key, _ = new_acct.find_program_address(
        seeds=[bytes(new_acct), bytes(TOKEN_PROGRAM_ID), bytes(test_mint)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    token_account_pubkey = spl_token.get_associated_token_address(new_acct, test_mint)
    assert token_account_pubkey == expected_token_account_key


@pytest.mark.integration
async def test_get_account_info(
    async_stubbed_sender_for_token: Keypair,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test get token account info."""
    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert account_data.state != 0  # is_initialized
    assert Pubkey(account_data.mint) == test_mint
    assert Pubkey(account_data.owner) == async_stubbed_sender_for_token.pubkey()
    assert account_data.amount == 0
    assert account_data.delegate_option == 0
    assert account_data.delegated_amount == 0
    assert account_data.state != 2  # not frozen
    assert account_data.is_native_option == 0
    assert account_data.close_authority_option == 0


@pytest.mark.integration
async def test_get_mint_info(
    async_stubbed_sender_for_token: Keypair,
    freeze_authority: Keypair,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test get token mint info."""
    info = await test_http_client_async.get_account_info(test_mint)
    assert_valid_response(info)
    mint_data = layouts.MINT_LAYOUT.parse(info.value.data)
    assert Pubkey(mint_data.mint_authority) == async_stubbed_sender_for_token.pubkey()
    assert mint_data.supply == 0
    assert mint_data.decimals == 6
    assert mint_data.is_initialized != 0
    assert Pubkey(mint_data.freeze_authority) == freeze_authority.pubkey()


@pytest.mark.integration
async def test_mint_to(
    async_stubbed_sender_for_token: Keypair,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test mint token to account and get balance."""
    expected_amount = 1000
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.mint_to(
        spl_token.models.MintToParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=test_mint,
            dest=sender_token_account,
            mint_authority=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    balance_resp = await test_http_client_async.get_token_account_balance(
        sender_token_account
    )
    balance_info = balance_resp.value
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == 6
    assert balance_info.ui_amount == 0.001


@pytest.mark.integration
async def test_transfer(
    async_stubbed_sender_for_token: Keypair,
    receiver_token_account: Pubkey,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test token transfer."""
    expected_amount = 500
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.transfer(
        spl_token.models.TransferParams(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_token_account,
            dest=receiver_token_account,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    balance_resp = await test_http_client_async.get_token_account_balance(
        receiver_token_account
    )
    balance_info = balance_resp.value
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == 6
    assert balance_info.ui_amount == 0.0005


@pytest.mark.integration
async def test_burn(
    async_stubbed_sender_for_token: Keypair,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test burning tokens."""
    burn_amount = 200
    expected_amount = 300
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.burn(
        spl_token.models.BurnParams(
            program_id=TOKEN_PROGRAM_ID,
            account=sender_token_account,
            mint=test_mint,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=burn_amount,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    balance_resp = await test_http_client_async.get_token_account_balance(
        sender_token_account
    )
    balance_info = balance_resp.value
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == 6
    assert balance_info.ui_amount == 0.0003


@pytest.mark.integration
async def test_mint_to_checked(
    async_stubbed_sender_for_token: Keypair,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test mint token checked and get balance."""
    expected_amount = 1000
    mint_amount = 700
    expected_decimals = 6
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.mint_to_checked(
        spl_token.models.MintToCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=test_mint,
            dest=sender_token_account,
            mint_authority=async_stubbed_sender_for_token.pubkey(),
            amount=mint_amount,
            decimals=expected_decimals,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    balance_resp = await test_http_client_async.get_token_account_balance(
        sender_token_account
    )
    balance_info = balance_resp.value
    assert balance_info.amount == str(expected_amount)
    assert balance_info.decimals == expected_decimals
    assert balance_info.ui_amount == 0.001


@pytest.mark.integration
async def test_transfer_checked(
    async_stubbed_sender_for_token: Keypair,
    receiver_token_account: Pubkey,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test token transfer checked."""
    transfer_amount = 500
    total_amount = 1000
    expected_decimals = 6
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.transfer_checked(
        spl_token.models.TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_token_account,
            mint=test_mint,
            dest=receiver_token_account,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=transfer_amount,
            decimals=expected_decimals,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    balance_resp = await test_http_client_async.get_token_account_balance(
        receiver_token_account
    )
    balance_info = balance_resp.value
    assert balance_info.amount == str(total_amount)
    assert balance_info.decimals == expected_decimals
    assert balance_info.ui_amount == 0.001


@pytest.mark.integration
async def test_burn_checked(
    async_stubbed_sender_for_token: Keypair,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test burning tokens checked."""
    burn_amount = 500
    expected_decimals = 6
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.burn_checked(
        spl_token.models.BurnCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            account=sender_token_account,
            mint=test_mint,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=burn_amount,
            decimals=expected_decimals,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    balance_resp = await test_http_client_async.get_token_account_balance(
        sender_token_account
    )
    balance_info = balance_resp.value
    assert balance_info.amount == str(0)
    assert balance_info.decimals == expected_decimals
    assert balance_info.ui_amount == 0.0


@pytest.mark.integration
async def test_get_accounts(
    async_stubbed_sender_for_token: Keypair,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test get token accounts."""
    resp = await test_http_client_async.get_token_accounts_by_owner_json_parsed(
        async_stubbed_sender_for_token.pubkey(),
        TokenAccountOpts(mint=test_mint),
    )
    assert_valid_response(resp)
    assert len(resp.value) >= 1
    for resp_data in resp.value:
        assert resp_data.pubkey
        parsed_data = resp_data.account.data.parsed["info"]
        assert parsed_data["owner"] == str(async_stubbed_sender_for_token.pubkey())


@pytest.mark.integration
async def test_approve(
    async_stubbed_sender_for_token: Keypair,
    async_stubbed_receiver: Pubkey,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test approval for delegating a token account."""
    expected_amount_delegated = 500
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.approve(
        spl_token.models.ApproveParams(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_token_account,
            delegate=async_stubbed_receiver,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount_delegated,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert Pubkey(account_data.delegate) == async_stubbed_receiver
    assert account_data.delegated_amount == expected_amount_delegated


@pytest.mark.integration
async def test_revoke(
    async_stubbed_sender_for_token: Keypair,
    async_stubbed_receiver: Pubkey,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test revoke for undelegating a token account."""
    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert Pubkey(account_data.delegate) == async_stubbed_receiver
    assert account_data.delegated_amount == 500

    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.revoke(
        spl_token.models.RevokeParams(
            program_id=TOKEN_PROGRAM_ID,
            account=sender_token_account,
            owner=async_stubbed_sender_for_token.pubkey(),
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert account_data.delegate_option == 0
    assert account_data.delegated_amount == 0


@pytest.mark.integration
async def test_approve_checked(
    async_stubbed_sender_for_token: Keypair,
    async_stubbed_receiver: Pubkey,
    sender_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test approve_checked for delegating a token account."""
    expected_amount_delegated = 500
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.approve_checked(
        spl_token.models.ApproveCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_token_account,
            mint=test_mint,
            delegate=async_stubbed_receiver,
            owner=async_stubbed_sender_for_token.pubkey(),
            amount=expected_amount_delegated,
            decimals=6,
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert Pubkey(account_data.delegate) == async_stubbed_receiver
    assert account_data.delegated_amount == expected_amount_delegated


@pytest.mark.integration
async def test_freeze_account(
    sender_token_account: Pubkey,
    freeze_authority: Keypair,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test freezing an account."""
    # Fund freeze authority
    resp = await test_http_client_async.request_airdrop(
        freeze_authority.pubkey(), AIRDROP_AMOUNT
    )
    await test_http_client_async.confirm_transaction(resp.value)

    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert account_data.state != 2  # not frozen

    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.freeze_account(
        spl_token.models.FreezeAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=sender_token_account,
            mint=test_mint,
            authority=freeze_authority.pubkey(),
        )
    )
    msg = MessageV0.try_compile(
        payer=freeze_authority.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [freeze_authority])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    await test_http_client_async.confirm_transaction(resp.value)

    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert account_data.state == 2  # frozen


@pytest.mark.integration
async def test_thaw_account(
    sender_token_account: Pubkey,
    freeze_authority: Keypair,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test thawing an account."""
    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert account_data.state == 2  # frozen

    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.thaw_account(
        spl_token.models.ThawAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=sender_token_account,
            mint=test_mint,
            authority=freeze_authority.pubkey(),
        )
    )
    msg = MessageV0.try_compile(
        payer=freeze_authority.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [freeze_authority])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    await test_http_client_async.confirm_transaction(resp.value)

    info = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info)
    account_data = layouts.ACCOUNT_LAYOUT.parse(info.value.data)
    assert account_data.state != 2  # not frozen


@pytest.mark.integration
async def test_close_account(
    async_stubbed_sender_for_token: Keypair,
    sender_token_account: Pubkey,
    receiver_token_account: Pubkey,
    test_mint: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test closing a token account."""
    create_resp = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(create_resp)
    assert create_resp.value.data

    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ix = spl_token.close_account(
        spl_token.models.CloseAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            account=sender_token_account,
            dest=receiver_token_account,
            owner=async_stubbed_sender_for_token.pubkey(),
        )
    )
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    info_resp = await test_http_client_async.get_account_info(sender_token_account)
    assert_valid_response(info_resp)
    assert info_resp.value is None


@pytest.mark.integration
async def test_create_multisig(
    async_stubbed_sender_for_token: Keypair,
    async_stubbed_receiver: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test creating a multisig account."""
    min_signers = 2
    multisig_keypair = Keypair()
    space = layouts.MULTISIG_LAYOUT.sizeof()
    balance_needed = (
        await test_http_client_async.get_minimum_balance_for_rent_exemption(space)
    ).value
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash

    ixs = [
        create_account(
            CreateAccountParams(
                from_pubkey=async_stubbed_sender_for_token.pubkey(),
                to_pubkey=multisig_keypair.pubkey(),
                lamports=balance_needed,
                space=space,
                owner=TOKEN_PROGRAM_ID,
            )
        ),
        spl_token.initialize_multisig(
            spl_token.models.InitializeMultisigParams(
                program_id=TOKEN_PROGRAM_ID,
                multisig=multisig_keypair.pubkey(),
                m=min_signers,
                signers=[
                    async_stubbed_sender_for_token.pubkey(),
                    async_stubbed_receiver,
                ],
            )
        ),
    ]
    msg = MessageV0.try_compile(
        payer=async_stubbed_sender_for_token.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    txn = VersionedTransaction(msg, [async_stubbed_sender_for_token, multisig_keypair])
    resp = await test_http_client_async.send_transaction(txn, opts=OPTS)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)

    info = await test_http_client_async.get_account_info(multisig_keypair.pubkey())
    assert_valid_response(info)
    assert info.value.owner == TOKEN_PROGRAM_ID

    multisig_data = layouts.MULTISIG_LAYOUT.parse(info.value.data)
    assert multisig_data.is_initialized
    assert multisig_data.m == min_signers
    assert Pubkey(multisig_data.signer1) == async_stubbed_sender_for_token.pubkey()
    assert Pubkey(multisig_data.signer2) == async_stubbed_receiver
