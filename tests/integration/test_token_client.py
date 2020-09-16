"""Tests for the SPL Token Client."""
import pytest

import spl.token._layouts as layouts
from solana.account import Account
from solana.publickey import PublicKey
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID

from .utils import assert_valid_response, confirm_transaction, decode_byte_string


@pytest.mark.integration
def test_create_mint(stubbed_sender, test_http_client):
    """Test create mint."""
    resp = test_http_client.request_airdrop(stubbed_sender.public_key(), 10000000)
    assert_valid_response(confirm_transaction(test_http_client, resp["result"]))

    expected_decimals = 6
    expected_freeze_authority = Account()
    actual = Token.create_mint(
        test_http_client,
        stubbed_sender,
        stubbed_sender.public_key(),
        expected_decimals,
        TOKEN_PROGRAM_ID,
        expected_freeze_authority.public_key(),
    )

    assert actual.pubkey
    assert actual.program_id == TOKEN_PROGRAM_ID
    assert actual.payer.public_key() == stubbed_sender.public_key()

    resp = test_http_client.get_account_info(actual.pubkey)
    assert_valid_response(resp)
    assert resp["result"]["value"]["owner"] == str(TOKEN_PROGRAM_ID)

    mint_data = layouts.MINT_LAYOUT.parse(decode_byte_string(resp["result"]["value"]["data"][0]))
    assert mint_data.is_initialized
    assert mint_data.decimals == expected_decimals
    assert mint_data.supply == 0
    assert PublicKey(mint_data.mint_authority) == stubbed_sender.public_key()
    assert PublicKey(mint_data.freeze_authority) == expected_freeze_authority.public_key()
