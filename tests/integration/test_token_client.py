"""Tests for the SPL Token Client."""
import pytest

import spl.token._layouts as layouts
from solana.account import Account
from solana.publickey import PublicKey
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID

from .utils import assert_valid_response, confirm_transaction, decode_byte_string


@pytest.mark.integration
@pytest.fixture(scope="module")
def test_token(stubbed_sender, test_http_client) -> Token:
    """Test create mint."""
    resp = test_http_client.request_airdrop(stubbed_sender.public_key(), 10000000)
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
