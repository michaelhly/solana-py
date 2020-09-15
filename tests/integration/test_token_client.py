"""Tests for the SPL Token Client."""
import pytest

from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID


@pytest.mark.integration
def test_create_mint(stubbed_sender, test_http_client):
    """Test create mint."""
    decimals = 6

    test_http_client.request_airdrop(stubbed_sender.public_key(), 100000)
    actual = Token.create_mint(
        test_http_client, stubbed_sender, stubbed_sender.public_key(), decimals, TOKEN_PROGRAM_ID
    )

    assert actual.pubkey
    assert actual.program_id == TOKEN_PROGRAM_ID
    assert actual.payer.public_key() == stubbed_sender.public_key()

    assert test_http_client.get_account_info(actual.pubkey) == 1
