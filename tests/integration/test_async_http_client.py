"""Tests for the HTTP API Client."""
import pytest

import solana.system_program as sp
from solana.rpc.api import DataSliceOpt
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.rpc.core import RPCException
from solana.rpc.types import RPCError
from solana.transaction import Transaction
from solana.rpc.commitment import Finalized
from spl.token.constants import WRAPPED_SOL_MINT

from .utils import AIRDROP_AMOUNT, assert_valid_response


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_air_drop(async_stubbed_sender: Keypair, test_http_client_async: AsyncClient):
    """Test air drop to async_stubbed_sender."""
    resp = await test_http_client_async.request_airdrop(async_stubbed_sender.public_key, AIRDROP_AMOUNT)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp["result"])
    balance = await test_http_client_async.get_balance(async_stubbed_sender.public_key)
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_air_drop_prefetched_blockhash(async_stubbed_sender_prefetched_blockhash, test_http_client_async):
    """Test air drop to async_stubbed_sender."""
    resp = await test_http_client_async.request_airdrop(
        async_stubbed_sender_prefetched_blockhash.public_key, AIRDROP_AMOUNT
    )
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp["result"])
    balance = await test_http_client_async.get_balance(async_stubbed_sender_prefetched_blockhash.public_key)
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_air_drop_cached_blockhash(
    async_stubbed_sender_cached_blockhash, test_http_client_async_cached_blockhash
):
    """Test air drop to async_stubbed_sender."""
    resp = await test_http_client_async_cached_blockhash.request_airdrop(
        async_stubbed_sender_cached_blockhash.public_key, AIRDROP_AMOUNT
    )
    assert_valid_response(resp)
    await test_http_client_async_cached_blockhash.confirm_transaction(resp["result"])
    balance = await test_http_client_async_cached_blockhash.get_balance(
        async_stubbed_sender_cached_blockhash.public_key
    )
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_invalid_transaction(test_http_client_async):
    """Test sending an invalid transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_receiver
    with pytest.raises(RPCException) as exc_info:
        await test_http_client_async.send_raw_transaction(b"foo")
    assert exc_info.value.args[0].keys() == RPCError.__annotations__.keys()  # pylint: disable=no-member


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_transaction_and_get_balance(async_stubbed_sender, async_stubbed_receiver, test_http_client_async):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to async_stubbed_receiver
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=async_stubbed_sender.public_key, to_pubkey=async_stubbed_receiver, lamports=1000
            )
        )
    )
    resp = await test_http_client_async.send_transaction(transfer_tx, async_stubbed_sender)
    assert_valid_response(resp)
    # Confirm transaction
    await test_http_client_async.confirm_transaction(resp["result"])
    # Check balances
    resp = await test_http_client_async.get_balance(async_stubbed_sender.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000
    resp = await test_http_client_async.get_balance(async_stubbed_receiver)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_transaction_prefetched_blockhash(
    async_stubbed_sender_prefetched_blockhash, async_stubbed_receiver_prefetched_blockhash, test_http_client_async
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to async_stubbed_receiver
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=async_stubbed_sender_prefetched_blockhash.public_key,
                to_pubkey=async_stubbed_receiver_prefetched_blockhash,
                lamports=1000,
            )
        )
    )
    resp = await test_http_client_async.send_transaction(transfer_tx, async_stubbed_sender_prefetched_blockhash)
    assert_valid_response(resp)
    # Confirm transaction
    await test_http_client_async.confirm_transaction(resp["result"])
    # Check balances
    resp = await test_http_client_async.get_balance(async_stubbed_sender_prefetched_blockhash.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000
    resp = await test_http_client_async.get_balance(async_stubbed_receiver_prefetched_blockhash)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_transaction_cached_blockhash(
    async_stubbed_sender_cached_blockhash,
    async_stubbed_receiver_cached_blockhash,
    test_http_client_async_cached_blockhash,
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_receiver
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=async_stubbed_sender_cached_blockhash.public_key,
                to_pubkey=async_stubbed_receiver_cached_blockhash,
                lamports=1000,
            )
        )
    )
    assert len(test_http_client_async_cached_blockhash.blockhash_cache.unused_blockhashes) == 0
    assert len(test_http_client_async_cached_blockhash.blockhash_cache.used_blockhashes) == 0
    resp = await test_http_client_async_cached_blockhash.send_transaction(
        transfer_tx, async_stubbed_sender_cached_blockhash
    )
    # we could have got a new blockhash or not depending on network latency and luck
    assert len(test_http_client_async_cached_blockhash.blockhash_cache.unused_blockhashes) in (0, 1)
    assert len(test_http_client_async_cached_blockhash.blockhash_cache.used_blockhashes) == 1
    assert_valid_response(resp)
    # Confirm transaction
    await test_http_client_async_cached_blockhash.confirm_transaction(resp["result"])
    # Check balances
    resp = await test_http_client_async_cached_blockhash.get_balance(async_stubbed_sender_cached_blockhash.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000

    # Second transaction
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=async_stubbed_sender_cached_blockhash.public_key,
                to_pubkey=async_stubbed_receiver_cached_blockhash,
                lamports=2000,
            )
        )
    )
    resp = await test_http_client_async_cached_blockhash.get_balance(async_stubbed_receiver_cached_blockhash)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954
    resp = await test_http_client_async_cached_blockhash.send_transaction(
        transfer_tx, async_stubbed_sender_cached_blockhash
    )
    # we could have got a new blockhash or not depending on network latency and luck
    assert len(test_http_client_async_cached_blockhash.blockhash_cache.unused_blockhashes) in (0, 1)
    assert len(test_http_client_async_cached_blockhash.blockhash_cache.used_blockhashes) in (1, 2)
    assert_valid_response(resp)
    # Confirm transaction
    resp = await test_http_client_async_cached_blockhash.confirm_transaction(resp["result"])
    # Check balances
    resp = await test_http_client_async_cached_blockhash.get_balance(async_stubbed_sender_cached_blockhash.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999987000


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_raw_transaction_and_get_balance(
    async_stubbed_sender, async_stubbed_receiver, test_http_client_async
):
    """Test sending a raw transaction to localnet."""
    # Get a recent blockhash
    resp = await test_http_client_async.get_recent_blockhash(Finalized)
    assert_valid_response(resp)
    recent_blockhash = resp["result"]["value"]["blockhash"]
    # Create transfer tx transfer lamports from stubbed sender to async_stubbed_receiver
    transfer_tx = Transaction(recent_blockhash=recent_blockhash).add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=async_stubbed_sender.public_key, to_pubkey=async_stubbed_receiver, lamports=1000
            )
        )
    )
    # Sign transaction
    transfer_tx.sign(async_stubbed_sender)
    # Send raw transaction
    resp = await test_http_client_async.send_raw_transaction(transfer_tx.serialize())
    assert_valid_response(resp)
    # Confirm transaction
    resp = await test_http_client_async.confirm_transaction(resp["result"])
    # Check balances
    resp = await test_http_client_async.get_balance(async_stubbed_sender.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999988000
    resp = await test_http_client_async.get_balance(async_stubbed_receiver)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 1954


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_bad_signature(test_http_client_async: AsyncClient) -> None:
    """Test that RPCException is raised when trying to confirm an invalid signature."""
    with pytest.raises(RPCException) as exc_info:
        await test_http_client_async.confirm_transaction("foo")
    err_object = exc_info.value.args[0]
    assert err_object == {"code": -32602, "message": "Invalid param: WrongSize"}


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
    resp = await test_http_client_async.get_recent_blockhash(Finalized)
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
async def test_get_token_largest_accounts(test_http_client_async):
    """Test get token largest accounts."""
    resp = await test_http_client_async.get_token_largest_accounts(WRAPPED_SOL_MINT)
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_token_supply(test_http_client_async):
    """Test get token supply."""
    resp = await test_http_client_async.get_token_supply(WRAPPED_SOL_MINT)
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
async def test_get_account_info(async_stubbed_sender, test_http_client_async):
    """Test get_account_info."""
    resp = await test_http_client_async.get_account_info(async_stubbed_sender.public_key)
    assert_valid_response(resp)
    resp = await test_http_client_async.get_account_info(async_stubbed_sender.public_key, encoding="jsonParsed")
    assert_valid_response(resp)
    resp = await test_http_client_async.get_account_info(async_stubbed_sender.public_key, data_slice=DataSliceOpt(1, 1))
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_multiple_accounts(async_stubbed_sender, test_http_client_async):
    """Test get_multiple_accounts."""
    pubkeys = [async_stubbed_sender.public_key] * 2
    resp = await test_http_client_async.get_multiple_accounts(pubkeys)
    assert_valid_response(resp)
    resp = await test_http_client_async.get_multiple_accounts(pubkeys, encoding="jsonParsed")
    assert_valid_response(resp)
    resp = await test_http_client_async.get_multiple_accounts(pubkeys, data_slice=DataSliceOpt(1, 1))
    assert_valid_response(resp)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_vote_accounts(test_http_client_async):
    """Test get vote accounts."""
    resp = await test_http_client_async.get_vote_accounts()
    assert_valid_response(resp)
