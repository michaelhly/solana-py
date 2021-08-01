"""Tests for the HTTP API Client."""
import pytest

import solana.system_program as sp
from solana.rpc.api import DataSliceOpt
from solana.transaction import Transaction

from .utils import assert_valid_response, confirm_transaction, aconfirm_transaction, compare_responses_without_ids


@pytest.mark.integration
def test_request_air_drop(stubbed_sender, test_http_clients):
    """Test air drop to stubbed_sender."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.request_airdrop(stubbed_sender.public_key(), 10000000000)
    async_resp = loop.run_until_complete(
        test_http_clients.async_.request_airdrop(stubbed_sender.public_key(), 10000000000)
    )
    assert resp == async_resp
    assert_valid_response(resp)
    resp = confirm_transaction(test_http_clients.sync, resp["result"])
    async_resp = loop.run_until_complete(aconfirm_transaction(test_http_clients.async_, async_resp["result"]))
    compare_responses_without_ids(resp, async_resp)
    assert_valid_response(resp)
    expected_meta = {
        "err": None,
        "fee": 0,
        "innerInstructions": [],
        "logMessages": [
            "Program 11111111111111111111111111111111 invoke [1]",
            "Program 11111111111111111111111111111111 success",
        ],
        "postBalances": [499999990000000000, 10000000000, 1],
        "postTokenBalances": [],
        "preBalances": [500000000000000000, 0, 1],
        "preTokenBalances": [],
        "rewards": [],
        "status": {"Ok": None},
    }
    assert resp["result"]["meta"] == expected_meta


@pytest.mark.integration
def test_send_transaction_and_get_balance(stubbed_sender, stubbed_reciever, test_http_clients):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_reciever
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(from_pubkey=stubbed_sender.public_key(), to_pubkey=stubbed_reciever, lamports=1000)
        )
    )
    loop = test_http_clients.loop
    resp = test_http_clients.sync.send_transaction(transfer_tx, stubbed_sender)
    async_resp = loop.run_until_complete(test_http_clients.async_.send_transaction(transfer_tx, stubbed_sender))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    # Confirm transaction
    resp = confirm_transaction(test_http_clients.sync, resp["result"])
    async_resp = loop.run_until_complete(aconfirm_transaction(test_http_clients.async_, async_resp["result"]))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    expected_meta = {
        "err": None,
        "fee": 5000,
        "innerInstructions": [],
        "logMessages": [
            "Program 11111111111111111111111111111111 invoke [1]",
            "Program 11111111111111111111111111111111 success",
        ],
        "postBalances": [9999994000, 954, 1],
        "postTokenBalances": [],
        "preBalances": [10000000000, 0, 1],
        "preTokenBalances": [],
        "rewards": [
            {
                "commission": None,
                "lamports": -46,
                "postBalance": 954,
                "pubkey": "J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99",
                "rewardType": "Rent",
            }
        ],
        "status": {"Ok": None},
    }
    assert resp["result"]["meta"] == expected_meta
    # Check balances
    resp = test_http_clients.sync.get_balance(stubbed_sender.public_key())
    async_resp = loop.run_until_complete(test_http_clients.async_.get_balance(stubbed_sender.public_key()))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    assert resp["result"]["value"] == 9999994000
    resp = test_http_clients.sync.get_balance(stubbed_reciever)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_balance(stubbed_reciever))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    assert resp["result"]["value"] == 954


@pytest.mark.integration
def test_send_raw_transaction_and_get_balance(stubbed_sender, stubbed_reciever, test_http_clients):
    """Test sending a raw transaction to localnet."""
    # Get a recent blockhash
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_recent_blockhash()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_recent_blockhash())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
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
    resp = test_http_clients.sync.send_raw_transaction(transfer_tx.serialize())
    async_resp = loop.run_until_complete(test_http_clients.async_.send_raw_transaction(transfer_tx.serialize()))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    # Confirm transaction
    resp = confirm_transaction(test_http_clients.sync, resp["result"])
    async_resp = loop.run_until_complete(aconfirm_transaction(test_http_clients.async_, async_resp["result"]))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    expected_meta = {
        "err": None,
        "fee": 5000,
        "innerInstructions": [],
        "logMessages": [
            "Program 11111111111111111111111111111111 invoke [1]",
            "Program 11111111111111111111111111111111 success",
        ],
        "postBalances": [9999988000, 1954, 1],
        "postTokenBalances": [],
        "preBalances": [9999994000, 954, 1],
        "preTokenBalances": [],
        "rewards": [],
        "status": {"Ok": None},
    }
    assert resp["result"]["meta"] == expected_meta
    # Check balances
    resp = test_http_clients.sync.get_balance(stubbed_sender.public_key())
    async_resp = loop.run_until_complete(test_http_clients.async_.get_balance(stubbed_sender.public_key()))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    assert resp["result"]["value"] == 9999988000
    resp = test_http_clients.sync.get_balance(stubbed_reciever)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_balance(stubbed_reciever))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    assert resp["result"]["value"] == 1954


@pytest.mark.integration
def test_get_block_commitment(test_http_clients):
    """Test get block commitment."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_block_commitment(5)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_block_commitment(5))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_block_time(test_http_clients):
    """Test get block time."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_block_time(5)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_block_time(5))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_cluster_nodes(test_http_clients):
    """Test get cluster nodes."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_cluster_nodes()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_cluster_nodes())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_confirmed_block(test_http_clients):
    """Test get confirmed block."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_confirmed_block(1)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_confirmed_block(1))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_confirmed_block_with_encoding(test_http_clients):
    """Test get confrimed block with encoding."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_confirmed_block(1, encoding="base64")
    async_resp = loop.run_until_complete(test_http_clients.async_.get_confirmed_block(1, encoding="base64"))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_confirmed_blocks(test_http_clients):
    """Test get confirmed blocks."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_confirmed_blocks(5, 10)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_confirmed_blocks(5, 10))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_confirmed_signature_for_address2(test_http_clients):
    """Test get confirmed signature for address2."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_confirmed_signature_for_address2(
        "Vote111111111111111111111111111111111111111", limit=1
    )
    async_resp = loop.run_until_complete(
        test_http_clients.async_.get_confirmed_signature_for_address2(
            "Vote111111111111111111111111111111111111111", limit=1
        )
    )
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


# TODO(michael): This RPC call is only available in solana-core v1.7 or newer.
# @pytest.mark.integration
# def test_get_signatures_for_address(test_http_client):
#     """Test get signatures for addresses."""
#     resp = test_http_client.get_signatures_for_address("Vote111111111111111111111111111111111111111", limit=1)
#     assert_valid_response(resp)


@pytest.mark.integration
def test_get_epoch_info(test_http_clients):
    """Test get epoch info."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_epoch_info()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_epoch_info())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_epoch_schedule(test_http_clients):
    """Test get epoch schedule."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_epoch_schedule()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_epoch_schedule())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_fee_calculator_for_blockhash(test_http_clients):
    """Test get fee calculator for blockhash."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_recent_blockhash()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_recent_blockhash())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    resp = test_http_clients.sync.get_fee_calculator_for_blockhash(resp["result"]["value"]["blockhash"])
    async_resp = loop.run_until_complete(
        test_http_clients.async_.get_fee_calculator_for_blockhash(async_resp["result"]["value"]["blockhash"])
    )
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_slot(test_http_clients):
    """Test get slot."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_slot()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_slot())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_fees(test_http_clients):
    """Test get fees."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_fees()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_fees())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_first_available_block(test_http_clients):
    """Test get first available block."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_first_available_block()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_first_available_block())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_genesis_hash(test_http_clients):
    """Test get genesis hash."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_genesis_hash()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_genesis_hash())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_identity(test_http_clients):
    """Test get identity."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_identity()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_identity())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_inflation_governor(test_http_clients):
    """Test get inflation governor."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_inflation_governor()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_inflation_governor())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_inflation_rate(test_http_clients):
    """Test get inflation rate."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_inflation_rate()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_inflation_rate())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_largest_accounts(test_http_clients):
    """Test get largest accounts."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_largest_accounts()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_largest_accounts())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_leader_schedule(test_http_clients):
    """Test get leader schedule."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_leader_schedule()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_leader_schedule())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_minimum_balance_for_rent_exemption(test_http_clients):
    """Test get minimum balance for rent exemption."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_minimum_balance_for_rent_exemption(50)
    async_resp = loop.run_until_complete(test_http_clients.async_.get_minimum_balance_for_rent_exemption(50))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_slot_leader(test_http_clients):
    """Test get slot leader."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_slot_leader()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_slot_leader())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_supply(test_http_clients):
    """Test get slot leader."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_supply()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_supply())
    assert_valid_response(resp)
    assert resp["result"]["value"].keys() == async_resp["result"]["value"].keys()


@pytest.mark.integration
def test_get_transaction_count(test_http_clients):
    """Test get transactinon count."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_transaction_count()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_transaction_count())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_version(test_http_clients):
    """Test get version."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_version()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_version())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_account_info(stubbed_sender, test_http_clients):
    """Test get_account_info."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_account_info(stubbed_sender.public_key())
    async_resp = loop.run_until_complete(test_http_clients.async_.get_account_info(stubbed_sender.public_key()))
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    resp = test_http_clients.sync.get_account_info(stubbed_sender.public_key(), encoding="jsonParsed")
    async_resp = loop.run_until_complete(
        test_http_clients.async_.get_account_info(stubbed_sender.public_key(), encoding="jsonParsed")
    )
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
    resp = test_http_clients.sync.get_account_info(stubbed_sender.public_key(), data_slice=DataSliceOpt(1, 1))
    async_resp = loop.run_until_complete(
        test_http_clients.async_.get_account_info(stubbed_sender.public_key(), data_slice=DataSliceOpt(1, 1))
    )
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)


@pytest.mark.integration
def test_get_vote_accounts(test_http_clients):
    """Test get vote accounts."""
    loop = test_http_clients.loop
    resp = test_http_clients.sync.get_vote_accounts()
    async_resp = loop.run_until_complete(test_http_clients.async_.get_vote_accounts())
    assert_valid_response(resp)
    compare_responses_without_ids(resp, async_resp)
