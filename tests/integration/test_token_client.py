# pylint: disable=R0401
"""Tests for the SPL Token Client."""
import pytest

import spl.token._layouts as layouts
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from spl.token.client import Token
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

from .utils import AIRDROP_AMOUNT, assert_valid_response, confirm_transaction, decode_byte_string


@pytest.mark.integration
@pytest.fixture(scope="module")
def test_token(stubbed_sender, test_http_client) -> Token:
    """Test create mint."""
    resp = test_http_client.request_airdrop(stubbed_sender.public_key(), AIRDROP_AMOUNT)
    assert_valid_response(confirm_transaction(test_http_client, resp["result"]))

    expected_decimals = 6
    expected_freeze_authority = Account()
    token_client = Token.create_mint(
        test_http_client,
        stubbed_sender,
        stubbed_sender.public_key(),
        expected_decimals,
        TOKEN_PROGRAM_ID,
        expected_freeze_authority.public_key(),
    )

    assert token_client.pubkey
    assert token_client.program_id == TOKEN_PROGRAM_ID
    assert token_client.payer.public_key() == stubbed_sender.public_key()

    resp = test_http_client.get_account_info(token_client.pubkey)
    assert_valid_response(resp)
    assert resp["result"]["value"]["owner"] == str(TOKEN_PROGRAM_ID)

    mint_data = layouts.MINT_LAYOUT.parse(decode_byte_string(resp["result"]["value"]["data"][0]))
    assert mint_data.is_initialized
    assert mint_data.decimals == expected_decimals
    assert mint_data.supply == 0
    assert PublicKey(mint_data.mint_authority) == stubbed_sender.public_key()
    assert PublicKey(mint_data.freeze_authority) == expected_freeze_authority.public_key()
    return token_client


@pytest.mark.integration
@pytest.fixture(scope="module")
def stubbed_sender_token_account_pk(stubbed_sender, test_token) -> PublicKey:  # pylint: disable=redefined-outer-name
    """Token account for stubbed sender."""
    return test_token.create_account(stubbed_sender.public_key())


@pytest.mark.integration
@pytest.fixture(scope="module")
def stubbed_receiver_token_account_pk(
    stubbed_receiver, test_token  # pylint: disable=redefined-outer-name
) -> PublicKey:
    """Token account for stubbed reciever."""
    return test_token.create_account(stubbed_receiver)


@pytest.mark.integration
def test_new_account(stubbed_sender, test_http_client, test_token):  # pylint: disable=redefined-outer-name
    """Test creating a new token account."""
    token_account_pk = test_token.create_account(stubbed_sender.public_key())
    resp = test_http_client.get_account_info(token_account_pk)
    assert_valid_response(resp)
    assert resp["result"]["value"]["owner"] == str(TOKEN_PROGRAM_ID)

    account_data = layouts.ACCOUNT_LAYOUT.parse(decode_byte_string(resp["result"]["value"]["data"][0]))
    assert account_data.state
    assert not account_data.amount
    assert (
        not account_data.delegate_option
        and not account_data.delegated_amount
        and PublicKey(account_data.delegate) == PublicKey(0)
    )
    assert not account_data.close_authority_option and PublicKey(account_data.close_authority) == PublicKey(0)
    assert not account_data.is_native_option and not account_data.is_native
    assert PublicKey(account_data.mint) == test_token.pubkey
    assert PublicKey(account_data.owner) == stubbed_sender.public_key()


@pytest.mark.integration
def test_new_associated_account(test_token):  # pylint: disable=redefined-outer-name
    """Test creating a new associated token account."""
    new_acct = PublicKey(0)
    token_account_pubkey = test_token.create_associated_token_account(new_acct)
    expected_token_account_key, _ = new_acct.find_program_address(
        seeds=[bytes(new_acct), bytes(TOKEN_PROGRAM_ID), bytes(test_token.pubkey)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    assert token_account_pubkey == expected_token_account_key


@pytest.mark.integration
def test_mint_to(stubbed_sender, stubbed_sender_token_account_pk, test_token):  # pylint: disable=redefined-outer-name
    """Test mint token to account and get balance."""
    expected_amount = 1000
    assert_valid_response(
        test_token.mint_to(
            dest=stubbed_sender_token_account_pk,
            mint_authority=stubbed_sender,
            amount=1000,
            opts=TxOpts(skip_confirmation=False),
        )
    )
    resp = test_token.get_balance(stubbed_sender_token_account_pk)
    balance_info = resp["result"]["value"]
    assert balance_info["amount"] == str(expected_amount)
    assert balance_info["decimals"] == 6
    assert balance_info["uiAmount"] == 0.001


@pytest.mark.integration
def test_transfer(
    stubbed_sender, stubbed_receiver_token_account_pk, stubbed_sender_token_account_pk, test_token
):  # pylint: disable=redefined-outer-name
    """Test token transfer."""
    expected_amount = 500
    assert_valid_response(
        test_token.transfer(
            source=stubbed_sender_token_account_pk,
            dest=stubbed_receiver_token_account_pk,
            owner=stubbed_sender,
            amount=expected_amount,
            opts=TxOpts(skip_confirmation=False),
        )
    )
    resp = test_token.get_balance(stubbed_receiver_token_account_pk)
    balance_info = resp["result"]["value"]
    assert balance_info["amount"] == str(expected_amount)
    assert balance_info["decimals"] == 6
    assert balance_info["uiAmount"] == 0.0005


@pytest.mark.integration
def test_get_accounts(stubbed_sender, test_token):  # pylint: disable=redefined-outer-name
    """Test get token accounts."""
    resp = test_token.get_accounts(stubbed_sender.public_key())
    assert_valid_response(resp)
    assert len(resp["result"]["value"]) == 2
    for resp_data in resp["result"]["value"]:
        assert PublicKey(resp_data["pubkey"])
        parsed_data = resp_data["account"]["data"]["parsed"]["info"]
        assert parsed_data["owner"] == str(stubbed_sender.public_key())
