"""Tests for the HTTP API Client."""
import pytest

import solanarpc.api as sol_api
from solanarpc.rpc_types import RPCResponse
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
    actual = confirmed_resp["result"]
    expected_meta = {
        "err": None,
        "fee": 0,
        "postBalances": [499999999999990000, 9954, 1],
        "preBalances": [500000000000000000, 0, 1],
        "status": {"Ok": None},
    }
    assert actual["meta"] == expected_meta
    assert actual["slot"] == 2
    # Transfer lamports from stubbed sender to stubbed_reciever
    transfer = SystemProgram.transfer(
        TransferParams(from_pubkey=stubbed_sender.public_key(), to_pubkey=stubbed_reciever, lamports=1000)
    )
    tx_resp = http_client.send_transaction(transfer, stubbed_sender)
    confirmed_resp = confirm_transaction(http_client, tx_resp["result"])
    assert confirmed_resp["jsonrpc"] == "2.0"
    actual = confirmed_resp["result"]
    expected_meta = {
        "err": None,
        "fee": 5000,
        "postBalances": [3954, 954, 1],
        "preBalances": [9954, 0, 1],
        "status": {"Ok": None},
    }
    assert actual["meta"] == expected_meta
    assert actual["slot"] == 37
    # Check balances
    actual = http_client.get_balance(stubbed_sender.public_key())
    expected = RPCResponse({"jsonrpc": "2.0", "result": {"context": {"slot": 38}, "value": 3954}, "id": 9})
    assert actual == expected
    actual = http_client.get_balance(stubbed_reciever)
    expected = RPCResponse({"jsonrpc": "2.0", "result": {"context": {"slot": 38}, "value": 954}, "id": 10})
    assert actual == expected
