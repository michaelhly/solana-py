"""Tests for the HTTP API Client."""
import pytest

import solana.system_program as sp
from solana.rpc.api import DataSliceOpt
from solana.transaction import Transaction

from .utils import AIRDROP_AMOUNT, aconfirm_transaction, assert_valid_response, generate_expected_meta_after_airdrop


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_air_drop(alt_stubbed_sender, test_http_client_async):
    """Test air drop to alt_stubbed_sender."""
    resp = await test_http_client_async.request_airdrop(alt_stubbed_sender.public_key(), AIRDROP_AMOUNT)
    assert_valid_response(resp)
    resp = await aconfirm_transaction(test_http_client_async, resp["result"])
    assert_valid_response(resp)
    expected_meta = generate_expected_meta_after_airdrop(resp)
    assert resp["result"]["meta"] == expected_meta


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_transaction_and_get_balance(alt_stubbed_sender, alt_stubbed_receiver, test_http_client_async):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to alt_stubbed_receiver
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=alt_stubbed_sender.public_key(), to_pubkey=alt_stubbed_receiver, lamports=1000
            )
        )
    )
    resp = await test_http_client_async.send_transaction(transfer_tx, alt_stubbed_sender)
    assert_valid_response(resp)
    # Confirm transaction
    resp = await aconfirm_transaction(test_http_client_async, resp["result"])
    assert_valid_response(resp)
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
                "pubkey": "J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i98",
                "rewardType": "Rent",
            }
        ],
        "status": {"Ok": None},
    }
    assert resp["result"]["meta"] == expected_meta
    # Check balances
    resp = await test_http_client_async.get_balance(alt_stubbed_sender.public_key())
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000
    resp = await test_http_client_async.get_balance(alt_stubbed_receiver)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_raw_transaction_and_get_balance(alt_stubbed_sender, alt_stubbed_receiver, test_http_client_async):
    """Test sending a raw transaction to localnet."""
    # Get a recent blockhash
    resp = await test_http_client_async.get_recent_blockhash()
    assert_valid_response(resp)
    recent_blockhash = resp["result"]["value"]["blockhash"]
    # Create transfer tx transfer lamports from stubbed sender to alt_stubbed_receiver
    transfer_tx = Transaction(recent_blockhash=recent_blockhash).add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=alt_stubbed_sender.public_key(), to_pubkey=alt_stubbed_receiver, lamports=1000
            )
        )
    )
    # Sign transaction
    transfer_tx.sign(alt_stubbed_sender)
    # Send raw transaction
    resp = await test_http_client_async.send_raw_transaction(transfer_tx.serialize())
    assert_valid_response(resp)
    # Confirm transaction
    resp = await aconfirm_transaction(test_http_client_async, resp["result"])
    assert_valid_response(resp)
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
    resp = await test_http_client_async.get_balance(alt_stubbed_sender.public_key())
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999988000
    resp = await test_http_client_async.get_balance(alt_stubbed_receiver)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 1954


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_block_commitment(test_http_client_async):
    """Test get block commitment."""
    resp = await test_http_client_async.get_block_commitment(5)
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_block_time(test_http_client_async):
    """Test get block time."""
    resp = await test_http_client_async.get_block_time(5)
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_cluster_nodes(test_http_client_async):
    """Test get cluster nodes."""
    resp = await test_http_client_async.get_cluster_nodes()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_confirmed_block(test_http_client_async):
    """Test get confirmed block."""
    resp = await test_http_client_async.get_confirmed_block(1)
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_confirmed_block_with_encoding(test_http_client_async):
    """Test get confrimed block with encoding."""
    resp = await test_http_client_async.get_confirmed_block(1, encoding="base64")
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_confirmed_blocks(test_http_client_async):
    """Test get confirmed blocks."""
    resp = await test_http_client_async.get_confirmed_blocks(5, 10)
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_confirmed_signature_for_address2(test_http_client_async):
    """Test get confirmed signature for address2."""
    resp = await test_http_client_async.get_confirmed_signature_for_address2(
        "Vote111111111111111111111111111111111111111", limit=1
    )
    assert_valid_response(resp)


# TODO(michael): This RPC call is only available in solana-core v1.7 or newer.
# @pytest.mark.integration
# @pytest.mark.asyncio
# async def test_get_signatures_for_address(test_http_client_async_async):
#     """Test get signatures for addresses."""
#     resp = await test_http_client_async_async.get_signatures_for_address(
#         "Vote111111111111111111111111111111111111111", limit=1
#     )
#     assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_epoch_info(test_http_client_async):
    """Test get epoch info."""
    resp = await test_http_client_async.get_epoch_info()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_epoch_schedule(test_http_client_async):
    """Test get epoch schedule."""
    resp = await test_http_client_async.get_epoch_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_fee_calculator_for_blockhash(test_http_client_async):
    """Test get fee calculator for blockhash."""
    resp = await test_http_client_async.get_recent_blockhash()
    assert_valid_response(resp)
    resp = await test_http_client_async.get_fee_calculator_for_blockhash(resp["result"]["value"]["blockhash"])
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_slot(test_http_client_async):
    """Test get slot."""
    resp = await test_http_client_async.get_slot()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_fees(test_http_client_async):
    """Test get fees."""
    resp = await test_http_client_async.get_fees()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_first_available_block(test_http_client_async):
    """Test get first available block."""
    resp = await test_http_client_async.get_first_available_block()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_genesis_hash(test_http_client_async):
    """Test get genesis hash."""
    resp = await test_http_client_async.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_identity(test_http_client_async):
    """Test get identity."""
    resp = await test_http_client_async.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_inflation_governor(test_http_client_async):
    """Test get inflation governor."""
    resp = await test_http_client_async.get_inflation_governor()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_inflation_rate(test_http_client_async):
    """Test get inflation rate."""
    resp = await test_http_client_async.get_inflation_rate()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_largest_accounts(test_http_client_async):
    """Test get largest accounts."""
    resp = await test_http_client_async.get_largest_accounts()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_leader_schedule(test_http_client_async):
    """Test get leader schedule."""
    resp = await test_http_client_async.get_leader_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_minimum_balance_for_rent_exemption(test_http_client_async):
    """Test get minimum balance for rent exemption."""
    resp = await test_http_client_async.get_minimum_balance_for_rent_exemption(50)
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_slot_leader(test_http_client_async):
    """Test get slot leader."""
    resp = await test_http_client_async.get_slot_leader()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_supply(test_http_client_async):
    """Test get slot leader."""
    resp = await test_http_client_async.get_supply()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_transaction_count(test_http_client_async):
    """Test get transactinon count."""
    resp = await test_http_client_async.get_transaction_count()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_version(test_http_client_async):
    """Test get version."""
    resp = await test_http_client_async.get_version()
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_account_info(alt_stubbed_sender, test_http_client_async):
    """Test get_account_info."""
    resp = await test_http_client_async.get_account_info(alt_stubbed_sender.public_key())
    assert_valid_response(resp)
    resp = await test_http_client_async.get_account_info(alt_stubbed_sender.public_key(), encoding="jsonParsed")
    assert_valid_response(resp)
    resp = await test_http_client_async.get_account_info(alt_stubbed_sender.public_key(), data_slice=DataSliceOpt(1, 1))
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_vote_accounts(test_http_client_async):
    """Test get vote accounts."""
    resp = await test_http_client_async.get_vote_accounts()
    assert_valid_response(resp)
