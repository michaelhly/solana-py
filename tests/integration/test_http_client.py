"""Tests for the HTTP API Client."""
import pytest

import solana.system_program as sp
from solana.rpc.api import Client, DataSliceOpt
from solana.transaction import Transaction

from .utils import assert_valid_response, confirm_transaction


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client(docker_services) -> Client:
    """Test http_client.is_connected."""
    http_client = Client()
    docker_services.wait_until_responsive(timeout=15, pause=1, check=http_client.is_connected)
    return http_client


@pytest.mark.integration
def test_request_air_drop(
    stubbed_sender, test_http_client
):  # pylint: disable=redefined-outer-name  # pylint: disable=redefined-outer-name
    """Test air drop to stubbed_sender."""
    resp = test_http_client.request_airdrop(stubbed_sender.public_key(), 10000000000)
    assert_valid_response(resp)
    resp = confirm_transaction(test_http_client, resp["result"])
    assert_valid_response(resp)
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
):  # pylint: disable=redefined-outer-name  # pylint: disable=redefined-outer-name
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_reciever
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(from_pubkey=stubbed_sender.public_key(), to_pubkey=stubbed_reciever, lamports=1000)
        )
    )
    resp = test_http_client.send_transaction(transfer_tx, stubbed_sender)
    assert_valid_response(resp)
    # Confirm transaction
    resp = confirm_transaction(test_http_client, resp["result"])
    assert_valid_response(resp)
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
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000
    resp = test_http_client.get_balance(stubbed_reciever)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954


@pytest.mark.integration
def test_send_raw_transaction_and_get_balance(
    stubbed_sender, stubbed_reciever, test_http_client
):  # pylint: disable=redefined-outer-name  # pylint: disable=redefined-outer-name
    """Test sending a raw transaction to localnet."""
    # Get a recent blockhash
    resp = test_http_client.get_recent_blockhash()
    assert_valid_response(resp)
    recent_blockhash = resp["result"]["value"]["blockhash"]
    # Create transfer tx transfer lamports from stubbed sender to stubbed_reciever
    transfer_tx = Transaction(recent_blockhash=recent_blockhash).add(
        sp.transfer(
            sp.TransferParams(from_pubkey=stubbed_sender.public_key(), to_pubkey=stubbed_reciever, lamports=1000)
        )
    )
    # Sign transaction
    transfer_tx.sign(stubbed_sender)
    # Send raw transaction
    resp = test_http_client.send_raw_transaction(transfer_tx)
    assert_valid_response(resp)
    # Confirm transaction
    resp = confirm_transaction(test_http_client, resp["result"])
    assert_valid_response(resp)
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
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999988000
    resp = test_http_client.get_balance(stubbed_reciever)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 1954


@pytest.mark.integration
def test_get_block_commitment(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get block commitment."""
    resp = test_http_client.get_block_commitment(5)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_block_time(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get block time."""
    resp = test_http_client.get_block_time(5)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_cluster_nodes(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get cluster nodes."""
    resp = test_http_client.get_cluster_nodes()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_block(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get confirmed block."""
    resp = test_http_client.get_confirmed_block(1)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_block_with_encoding(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get confrimed block with encoding."""
    resp = test_http_client.get_confirmed_block(1, encoding="base64")
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_blocks(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get confirmed blocks."""
    resp = test_http_client.get_confirmed_blocks(5, 10)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_signature_for_address2(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get confirmed signature for address2."""
    resp = test_http_client.get_confirmed_signature_for_address2("Vote111111111111111111111111111111111111111", limit=1)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_epoch_info(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get epoch info."""
    resp = test_http_client.get_epoch_info()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_epoch_schedule(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get epoch schedule."""
    resp = test_http_client.get_epoch_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_fee_calculator_for_blockhash(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get fee calculator for blockhash."""
    resp = test_http_client.get_recent_blockhash()
    assert_valid_response(resp)
    resp = test_http_client.get_fee_calculator_for_blockhash(resp["result"]["value"]["blockhash"])
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_slot(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get slot."""
    resp = test_http_client.get_slot()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_fees(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get fees."""
    resp = test_http_client.get_fees()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_first_available_block(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get first available block."""
    resp = test_http_client.get_first_available_block()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_genesis_hash(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get genesis hash."""
    resp = test_http_client.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_identity(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get identity."""
    resp = test_http_client.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_inflation_governor(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get inflation governor."""
    resp = test_http_client.get_inflation_governor()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_inflation_rate(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get inflation rate."""
    resp = test_http_client.get_inflation_rate()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_largest_accounts(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get largest accounts."""
    resp = test_http_client.get_largest_accounts()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_leader_schedule(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get leader schedule."""
    resp = test_http_client.get_leader_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_minimum_balance_for_rent_exemption(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get minimum balance for rent exemption."""
    resp = test_http_client.get_minimum_balance_for_rent_exemption(50)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_slot_leader(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get slot leader."""
    resp = test_http_client.get_slot_leader()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_supply(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get slot leader."""
    resp = test_http_client.get_supply()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_transaction_count(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get transactinon count."""
    resp = test_http_client.get_transaction_count()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_version(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get version."""
    resp = test_http_client.get_version()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_account_info(stubbed_sender, test_http_client):  # pylint: disable=redefined-outer-name
    """Test get_account_info."""
    resp = test_http_client.get_account_info(stubbed_sender.public_key())
    assert_valid_response(resp)
    resp = test_http_client.get_account_info(stubbed_sender.public_key(), encoding="jsonParsed")
    assert_valid_response(resp)
    resp = test_http_client.get_account_info(stubbed_sender.public_key(), data_slice=DataSliceOpt(1, 1))
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_vote_accounts(test_http_client):  # pylint: disable=redefined-outer-name
    """Test get vote accounts."""
    resp = test_http_client.get_vote_accounts()
    assert_valid_response(resp)
