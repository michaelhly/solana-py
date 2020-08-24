"""Tests for the HTTP API Client."""
import pytest

import solanarpc.api as sol_api
from solanaweb3.system_program import SystemProgram, TransferParams

from .utils import confirm_transaction


@pytest.mark.integration_test
def test_send_transaction(docker_services, stubbed_sender, stubbed_reciever):
    """Test sending a transaction to localnet."""
    http_client = sol_api.Client(client_type=sol_api.HTTP)
    docker_services.wait_until_responsive(timeout=15, pause=1, check=http_client.is_connected)
    # Airdrop to stubbed sender
    tx_resp = http_client.request_airdrop(stubbed_sender.public_key(), 10000)
    confirmed_resp = confirm_transaction(http_client, tx_resp["result"])
    assert confirmed_resp["jsonrpc"] == "2.0"
    expected_meta = {
        "err": None,
        "fee": 0,
        "postBalances": [499999999999990000, 9954, 1],
        "preBalances": [500000000000000000, 0, 1],
        "status": {"Ok": None},
    }
    assert confirmed_resp["result"]["meta"] == expected_meta
    # Transfer lamports from stubbed sender to stubbed_reciever
    transfer = SystemProgram.transfer(
        TransferParams(from_pubkey=stubbed_sender.public_key(), to_pubkey=stubbed_reciever, lamports=1000)
    )
    tx_resp = http_client.send_transaction(transfer, stubbed_sender)
    confirmed_resp = confirm_transaction(http_client, tx_resp["result"])
    assert confirmed_resp["jsonrpc"] == "2.0"
    expected_meta = {
        "err": None,
        "fee": 5000,
        "postBalances": [3954, 954, 1],
        "preBalances": [9954, 0, 1],
        "status": {"Ok": None},
    }
    assert confirmed_resp["result"]["meta"] == expected_meta
    # Check balances
    resp = http_client.get_balance(stubbed_sender.public_key())
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]["value"] == 3954
    resp = http_client.get_balance(stubbed_reciever)
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]["value"] == 954
