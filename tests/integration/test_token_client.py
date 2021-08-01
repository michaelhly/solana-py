"""Tests for the SPL Token Client."""
from typing import NamedTuple
import pytest

import spl.token._layouts as layouts
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from spl.token.client import Token, AsyncToken
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

from .utils import (
    assert_valid_response,
    confirm_transaction,
    aconfirm_transaction,
    decode_byte_string,
)


class TokenClients(NamedTuple):
    """Container for sync and async token clients"""

    sync: Token
    async_: AsyncToken


class AccountKeys(NamedTuple):
    """Container for public keys"""

    sync: PublicKey
    async_: PublicKey


@pytest.mark.integration
@pytest.fixture(scope="module")
def test_token(stubbed_sender, alt_stubbed_sender, test_http_clients) -> TokenClients:
    """Test create mint."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.request_airdrop(stubbed_sender.public_key(), 10000000)
    async_resp = loop.run_until_complete(
        test_http_clients.async_.request_airdrop(alt_stubbed_sender.public_key(), 10000000)
    )
    assert_valid_response(confirm_transaction(test_http_clients.sync, resp["result"]))
    assert_valid_response(loop.run_until_complete(aconfirm_transaction(test_http_clients.async_, async_resp["result"])))

    expected_decimals = 6
    expected_freeze_authority = Account()
    token_client = Token.create_mint(
        test_http_clients.sync,
        stubbed_sender,
        stubbed_sender.public_key(),
        expected_decimals,
        TOKEN_PROGRAM_ID,
        expected_freeze_authority.public_key(),
    )
    async_token_client = loop.run_until_complete(
        AsyncToken.create_mint(
            test_http_clients.async_,
            alt_stubbed_sender,
            alt_stubbed_sender.public_key(),
            expected_decimals,
            TOKEN_PROGRAM_ID,
            expected_freeze_authority.public_key(),
        )
    )
    for idx, _token_client in enumerate([token_client, async_token_client]):
        assert _token_client.pubkey
        assert _token_client.program_id == TOKEN_PROGRAM_ID
        assert _token_client.payer.public_key() == {0: stubbed_sender, 1: alt_stubbed_sender}[idx].public_key()

    resp = test_http_clients.sync.get_account_info(token_client.pubkey)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_account_info(async_token_client.pubkey))
    for idx, _resp in enumerate([resp, async_resp]):
        assert_valid_response(_resp)
        assert _resp["result"]["value"]["owner"] == str(TOKEN_PROGRAM_ID)
        mint_data = layouts.MINT_LAYOUT.parse(decode_byte_string(_resp["result"]["value"]["data"][0]))
        assert mint_data.is_initialized
        assert mint_data.decimals == expected_decimals
        assert mint_data.supply == 0
        assert PublicKey(mint_data.mint_authority) == {0: stubbed_sender, 1: alt_stubbed_sender}[idx].public_key()
        assert PublicKey(mint_data.freeze_authority) == expected_freeze_authority.public_key()
    return TokenClients(sync=token_client, async_=async_token_client)


@pytest.mark.integration
@pytest.fixture(scope="module")
def stubbed_sender_token_account_pk(
    test_http_clients,
    stubbed_sender,
    alt_stubbed_sender,
    test_token,  # pylint: disable=redefined-outer-name
) -> AccountKeys:
    """Token account for stubbed sender."""
    loop = test_http_clients.loop
    sync = test_token.sync.create_account(stubbed_sender.public_key())
    async_ = loop.run_until_complete(test_token.async_.create_account(alt_stubbed_sender.public_key()))
    return AccountKeys(sync=sync, async_=async_)


@pytest.mark.integration
@pytest.fixture(scope="module")
def stubbed_reciever_token_account_pk(
    test_http_clients, stubbed_reciever, test_token  # pylint: disable=redefined-outer-name
) -> AccountKeys:
    """Token account for stubbed reciever."""
    loop = test_http_clients.loop
    sync = test_token.sync.create_account(stubbed_reciever)
    async_ = loop.run_until_complete(test_token.async_.create_account(stubbed_reciever))
    return AccountKeys(sync=sync, async_=async_)


@pytest.mark.integration
def test_new_account(
    stubbed_sender, alt_stubbed_sender, test_http_clients, test_token
):  # pylint: disable=redefined-outer-name
    """Test creating a new token account."""
    loop = test_http_clients.loop
    token_account_pk = test_token.sync.create_account(stubbed_sender.public_key())
    async_token_account_pk = loop.run_until_complete(test_token.async_.create_account(alt_stubbed_sender.public_key()))
    resp = test_http_clients.sync.get_account_info(token_account_pk)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_account_info(async_token_account_pk))
    for idx, _resp in enumerate([resp, async_resp]):
        assert_valid_response(_resp)
        assert _resp["result"]["value"]["owner"] == str(TOKEN_PROGRAM_ID)
        account_data = layouts.ACCOUNT_LAYOUT.parse(decode_byte_string(_resp["result"]["value"]["data"][0]))
        assert account_data.state
        assert not account_data.amount
        assert (
            not account_data.delegate_option
            and not account_data.delegated_amount
            and PublicKey(account_data.delegate) == PublicKey(0)
        )
        assert not account_data.close_authority_option and PublicKey(account_data.close_authority) == PublicKey(0)
        assert not account_data.is_native_option and not account_data.is_native
        assert PublicKey(account_data.mint) == {0: test_token.sync, 1: test_token.async_}[idx].pubkey
        assert PublicKey(account_data.owner) == {0: stubbed_sender, 1: alt_stubbed_sender}[idx].public_key()


@pytest.mark.integration
def test_new_associated_account(test_token, test_http_clients):  # pylint: disable=redefined-outer-name
    """Test creating a new associated token account."""
    loop = test_http_clients.loop
    new_acct = PublicKey(0)
    new_acct_async = PublicKey(1)
    token_account_pubkey = test_token.sync.create_associated_token_account(new_acct)
    async_token_account_pubkey = loop.run_until_complete(
        test_token.async_.create_associated_token_account(new_acct_async)
    )
    expected_token_account_key, _ = new_acct.find_program_address(
        seeds=[bytes(new_acct), bytes(TOKEN_PROGRAM_ID), bytes(test_token.sync.pubkey)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    async_expected_token_account_key, _ = new_acct_async.find_program_address(
        seeds=[bytes(new_acct_async), bytes(TOKEN_PROGRAM_ID), bytes(test_token.async_.pubkey)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    assert token_account_pubkey == expected_token_account_key
    assert async_token_account_pubkey == async_expected_token_account_key


@pytest.mark.integration
def test_mint_to(
    stubbed_sender, alt_stubbed_sender, stubbed_sender_token_account_pk, test_token, test_http_clients
):  # pylint: disable=redefined-outer-name
    """Test mint token to account and get balance."""
    loop = test_http_clients.loop
    expected_amount = 1000
    assert_valid_response(
        test_token.sync.mint_to(
            dest=stubbed_sender_token_account_pk.sync,
            mint_authority=stubbed_sender,
            amount=1000,
            opts=TxOpts(skip_confirmation=False),
        )
    )
    assert_valid_response(
        loop.run_until_complete(
            test_token.async_.mint_to(
                dest=stubbed_sender_token_account_pk.async_,
                mint_authority=alt_stubbed_sender,
                amount=1000,
                opts=TxOpts(skip_confirmation=False),
            )
        )
    )
    resp = test_token.sync.get_balance(stubbed_sender_token_account_pk.sync)
    async_resp = loop.run_until_complete(test_token.async_.get_balance(stubbed_sender_token_account_pk.async_))
    balance_info = resp["result"]["value"]
    async_balance_info = async_resp["result"]["value"]
    assert balance_info == async_balance_info
    assert balance_info["amount"] == str(expected_amount)
    assert balance_info["decimals"] == 6
    assert balance_info["uiAmount"] == 0.001


@pytest.mark.integration
def test_transfer(
    stubbed_sender,
    alt_stubbed_sender,
    stubbed_reciever_token_account_pk,
    stubbed_sender_token_account_pk,
    test_token,
    test_http_clients,
):  # pylint: disable=redefined-outer-name
    """Test token transfer."""
    loop = test_http_clients.loop
    expected_amount = 500
    assert_valid_response(
        test_token.sync.transfer(
            source=stubbed_sender_token_account_pk.sync,
            dest=stubbed_reciever_token_account_pk.sync,
            owner=stubbed_sender,
            amount=expected_amount,
            opts=TxOpts(skip_confirmation=False),
        )
    )
    assert_valid_response(
        loop.run_until_complete(
            test_token.async_.transfer(
                source=stubbed_sender_token_account_pk.async_,
                dest=stubbed_reciever_token_account_pk.async_,
                owner=alt_stubbed_sender,
                amount=expected_amount,
                opts=TxOpts(skip_confirmation=False),
            )
        )
    )
    resp = test_token.sync.get_balance(stubbed_reciever_token_account_pk.sync)
    async_resp = loop.run_until_complete(test_token.async_.get_balance(stubbed_reciever_token_account_pk.async_))
    balance_info = resp["result"]["value"]
    async_balance_info = async_resp["result"]["value"]
    assert balance_info == async_balance_info
    assert balance_info["amount"] == str(expected_amount)
    assert balance_info["decimals"] == 6
    assert balance_info["uiAmount"] == 0.0005


@pytest.mark.integration
def test_get_accounts(
    stubbed_sender, alt_stubbed_sender, test_token, test_http_clients
):  # pylint: disable=redefined-outer-name
    """Test get token accounts."""
    loop = test_http_clients.loop
    resp = test_token.sync.get_accounts(stubbed_sender.public_key())
    async_resp = loop.run_until_complete(test_token.async_.get_accounts(alt_stubbed_sender.public_key()))
    for idx, _resp in enumerate([resp, async_resp]):
        assert_valid_response(_resp)
        assert len(_resp["result"]["value"]) == 2
        for resp_data in _resp["result"]["value"]:
            assert PublicKey(resp_data["pubkey"])
            parsed_data = resp_data["account"]["data"]["parsed"]["info"]
            assert parsed_data["owner"] == str({0: stubbed_sender, 1: alt_stubbed_sender}[idx].public_key())
