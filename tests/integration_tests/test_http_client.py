"""Tests for the HTTP API Client."""
import pytest

from solanarpc.api import HTTP, Client
from solanaweb3.system_program import SystemProgram, TransferParams
from solanaweb3.transaction import Transaction

from .utils import confirm_transaction


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client(docker_services) -> Client:
    """Test http_client.is_connected."""
    http_client = Client(client_type=HTTP)
    docker_services.wait_until_responsive(timeout=15, pause=1, check=http_client.is_connected)
    return http_client


@pytest.mark.integration
def test_request_air_drop(stubbed_sender, test_http_client):  # pylint: disable=redefined-outer-name
    """Test air drop to stubbed_sender."""
    resp = test_http_client.request_airdrop(stubbed_sender.public_key(), 10000000000)
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]
    resp = confirm_transaction(test_http_client, resp["result"])
    expected_meta = {
        "err": None,
        "fee": 0,
        "postBalances": [499999990000000000, 10000000000, 1],
        "preBalances": [500000000000000000, 0, 1],
        "status": {"Ok": None},
    }
    assert resp["result"]["meta"] == expected_meta


@pytest.mark.integration
def test_send_transaction_and_get_balance(
    stubbed_sender, stubbed_reciever, test_http_client
):  # pylint: disable=redefined-outer-name
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_reciever
    transfer_tx = SystemProgram.transfer(
        TransferParams(from_pubkey=stubbed_sender.public_key(), to_pubkey=stubbed_reciever, lamports=1000)
    )
    resp = test_http_client.send_transaction(transfer_tx, stubbed_sender)
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]
    # Confirm transaction
    resp = confirm_transaction(test_http_client, resp["result"])
    assert resp["jsonrpc"] == "2.0"
    expected_meta = {
        "err": None,
        "fee": 5000,
        "postBalances": [9999994000, 954, 1],
        "preBalances": [10000000000, 0, 1],
        "status": {"Ok": None},
    }
    assert resp["result"]["meta"] == expected_meta
    # Check balances
    resp = test_http_client.get_balance(stubbed_sender.public_key())
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]["value"] == 9999994000
    resp = test_http_client.get_balance(stubbed_reciever)
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]["value"] == 954


@pytest.mark.integration
def test_send_raw_transaction_and_get_balance(
    stubbed_sender, stubbed_reciever, test_http_client
):  # pylint: disable=redefined-outer-name
    """Test sending a raw transaction to localnet."""
    # Get a recent blockhash
    resp = test_http_client.get_recent_blockhash()
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]
    recent_blockhash = resp["result"]["value"]["blockhash"]
    # Create transfer tx transfer lamports from stubbed sender to stubbed_reciever
    transfer_tx = Transaction(recent_blockhash=recent_blockhash).add(
        SystemProgram.transfer(
            TransferParams(from_pubkey=stubbed_sender.public_key(), to_pubkey=stubbed_reciever, lamports=1000)
        )
    )
    # Sign transaction
    transfer_tx.sign(stubbed_sender)
    # Send raw transaction
    resp = test_http_client.send_raw_transaction(transfer_tx)
    assert resp["jsonrpc"] == "2.0"
    print(resp)
    assert resp["result"]
    # Confirm transaction
    resp = confirm_transaction(test_http_client, resp["result"])
    assert resp["jsonrpc"] == "2.0"
    expected_meta = {
        "err": None,
        "fee": 5000,
        "postBalances": [9999988000, 1954, 1],
        "preBalances": [9999994000, 954, 1],
        "status": {"Ok": None},
    }
    assert resp["result"]["meta"] == expected_meta
    # Check balances
    resp = test_http_client.get_balance(stubbed_sender.public_key())
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]["value"] == 9999988000
    resp = test_http_client.get_balance(stubbed_reciever)
    assert resp["jsonrpc"] == "2.0"
    assert resp["result"]["value"] == 1954
