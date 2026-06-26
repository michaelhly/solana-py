"""Tests for the HTTP API Client."""

import asyncio
from time import monotonic

import pytest
from pydantic import BaseModel, Field
import solders.system_program as sp
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.rpc.errors import SendTransactionPreflightFailureMessage
from solders.transaction import VersionedTransaction
from spl.token.constants import WRAPPED_SOL_MINT

from solana.constants import VOTE_PROGRAM_ID
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment, Confirmed, Finalized, Processed
from solana.rpc.core import RPCException, TransactionExpiredBlockheightExceededError
from solana.rpc.jsonrpc import JsonRpcRequest
from solana.rpc.models import DataSliceOpts, TxOpts

from ..utils import AIRDROP_AMOUNT, assert_valid_response


async def _ensure_minimum_balance(client: AsyncClient, pubkey: Pubkey, minimum_balance: int) -> int:
    """Top up an account when needed and return its current balance."""
    balance_resp = await client.get_balance(pubkey)
    assert_valid_response(balance_resp)
    if balance_resp.value >= minimum_balance:
        return balance_resp.value

    airdrop_resp = await client.request_airdrop(pubkey, AIRDROP_AMOUNT)
    assert_valid_response(airdrop_resp)
    await client.confirm_transaction(airdrop_resp.value)

    refreshed_balance = await client.get_balance(pubkey)
    assert_valid_response(refreshed_balance)
    return refreshed_balance.value


@pytest.mark.integration
async def test_request_air_drop(
    test_http_client_async: AsyncClient,
):
    """Test air drop to async_stubbed_sender and async_stubbed_receiver."""
    sender = Keypair()
    receiver = Keypair().pubkey()
    sender_balance_before = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(sender_balance_before)
    receiver_balance_before = await test_http_client_async.get_balance(receiver)
    assert_valid_response(receiver_balance_before)
    # Airdrop to stubbed_sender
    resp = await test_http_client_async.request_airdrop(sender.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)
    balance = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(balance)
    assert balance.value == sender_balance_before.value + AIRDROP_AMOUNT
    # Airdrop to stubbed_receiver
    resp = await test_http_client_async.request_airdrop(receiver, AIRDROP_AMOUNT)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)
    balance = await test_http_client_async.get_balance(receiver)
    assert_valid_response(balance)
    assert balance.value == receiver_balance_before.value + AIRDROP_AMOUNT


@pytest.mark.integration
async def test_request_air_drop_prefetched_blockhash(
    test_http_client_async: AsyncClient,
):
    """Test air drop to async_stubbed_sender and async_stubbed_receiver."""
    sender = Keypair()
    receiver = Keypair().pubkey()
    sender_balance_before = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(sender_balance_before)
    receiver_balance_before = await test_http_client_async.get_balance(receiver)
    assert_valid_response(receiver_balance_before)
    # Airdrop to stubbed_sender
    resp = await test_http_client_async.request_airdrop(sender.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)
    balance = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(balance)
    assert balance.value == sender_balance_before.value + AIRDROP_AMOUNT
    # Airdrop to stubbed_receiver
    resp = await test_http_client_async.request_airdrop(receiver, AIRDROP_AMOUNT)
    assert_valid_response(resp)
    await test_http_client_async.confirm_transaction(resp.value)
    balance = await test_http_client_async.get_balance(receiver)
    assert_valid_response(balance)
    assert balance.value == receiver_balance_before.value + AIRDROP_AMOUNT


@pytest.mark.integration
async def test_send_transaction_and_get_balance(
    test_http_client_async: AsyncClient,
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to async_stubbed_receiver
    sender = Keypair()
    receiver = Keypair().pubkey()
    amount = 1000
    sender_balance_before = await _ensure_minimum_balance(test_http_client_async, sender.pubkey(), amount + 50_000)
    receiver_balance_before = await _ensure_minimum_balance(test_http_client_async, receiver, 1)
    ixs = [
        sp.transfer(
            sp.TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=receiver,
                lamports=amount,
            )
        )
    ]
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    msg = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    fee_resp = await test_http_client_async.get_fee_for_message(msg)
    assert_valid_response(fee_resp)
    assert fee_resp.value is not None
    transfer_tx = VersionedTransaction(msg, [sender])
    resp = await test_http_client_async.send_transaction(transfer_tx)
    assert_valid_response(resp)
    # Confirm transaction
    await test_http_client_async.confirm_transaction(resp.value)
    # Check balances
    sender_balance_resp = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(sender_balance_resp)
    assert sender_balance_resp.value == sender_balance_before - amount - fee_resp.value
    receiver_balance_resp = await test_http_client_async.get_balance(receiver)
    assert_valid_response(receiver_balance_resp)
    assert receiver_balance_resp.value == receiver_balance_before + amount


@pytest.mark.integration
async def test_send_versioned_transaction_and_get_balance(
    random_funded_keypair: Keypair, test_http_client_async: AsyncClient
):
    """Test sending a transaction to localnet."""
    receiver = Keypair()
    amount = 1_000_000
    sender_balance_before = await _ensure_minimum_balance(
        test_http_client_async, random_funded_keypair.pubkey(), amount + 50_000
    )
    receiver_balance_before = await test_http_client_async.get_balance(receiver.pubkey())
    assert_valid_response(receiver_balance_before)
    transfer_ix = sp.transfer(
        sp.TransferParams(
            from_pubkey=random_funded_keypair.pubkey(),
            to_pubkey=receiver.pubkey(),
            lamports=amount,
        )
    )
    recent_blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    msg = MessageV0.try_compile(
        payer=random_funded_keypair.pubkey(),
        instructions=[transfer_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    fee_resp = await test_http_client_async.get_fee_for_message(msg)
    assert_valid_response(fee_resp)
    assert fee_resp.value is not None
    transfer_tx = VersionedTransaction(msg, [random_funded_keypair])
    sim_resp = await test_http_client_async.simulate_transaction(transfer_tx)
    assert_valid_response(sim_resp)
    resp = await test_http_client_async.send_transaction(transfer_tx)
    assert_valid_response(resp)
    # Confirm transaction
    await test_http_client_async.confirm_transaction(resp.value)
    # Check balances
    sender_balance_resp = await test_http_client_async.get_balance(random_funded_keypair.pubkey())
    assert_valid_response(sender_balance_resp)
    assert sender_balance_resp.value == sender_balance_before - amount - fee_resp.value
    receiver_balance_resp = await test_http_client_async.get_balance(receiver.pubkey())
    assert_valid_response(receiver_balance_resp)
    assert receiver_balance_resp.value == receiver_balance_before.value + amount


@pytest.mark.integration
async def test_send_bad_transaction(stubbed_receiver: Pubkey, test_http_client_async: AsyncClient):
    """Test sending a transaction that errors."""
    poor_account = Keypair()
    airdrop_amount = 1000000
    airdrop_resp = await test_http_client_async.request_airdrop(poor_account.pubkey(), airdrop_amount)
    assert_valid_response(airdrop_resp)
    await test_http_client_async.confirm_transaction(airdrop_resp.value)
    balance = await test_http_client_async.get_balance(poor_account.pubkey())
    assert balance.value == airdrop_amount
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_receiver
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ixs = [
        sp.transfer(
            sp.TransferParams(
                from_pubkey=poor_account.pubkey(),
                to_pubkey=stubbed_receiver,
                lamports=airdrop_amount + 1,
            )
        )
    ]
    msg = MessageV0.try_compile(
        payer=poor_account.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    transfer_tx = VersionedTransaction(msg, [poor_account])
    with pytest.raises(RPCException) as exc_info:
        await test_http_client_async.send_transaction(transfer_tx)
    err = exc_info.value.args[0]
    assert isinstance(err, SendTransactionPreflightFailureMessage)
    assert err.data.logs


@pytest.mark.integration
async def test_send_transaction_prefetched_blockhash(
    test_http_client_async: AsyncClient,
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to async_stubbed_receiver
    sender = Keypair()
    receiver = Keypair().pubkey()
    amount = 1000
    sender_balance_before = await _ensure_minimum_balance(test_http_client_async, sender.pubkey(), amount + 50_000)
    receiver_balance_before = await _ensure_minimum_balance(test_http_client_async, receiver, 1)
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ixs = [
        sp.transfer(
            sp.TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=receiver,
                lamports=amount,
            )
        )
    ]
    msg = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    fee_resp = await test_http_client_async.get_fee_for_message(msg)
    assert_valid_response(fee_resp)
    assert fee_resp.value is not None
    transfer_tx = VersionedTransaction(msg, [sender])
    resp = await test_http_client_async.send_transaction(transfer_tx)
    assert_valid_response(resp)
    # Confirm transaction
    await test_http_client_async.confirm_transaction(resp.value)
    # Check balances
    resp = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(resp)
    assert resp.value == sender_balance_before - amount - fee_resp.value
    resp = await test_http_client_async.get_balance(receiver)
    assert_valid_response(resp)
    assert resp.value == receiver_balance_before + amount


@pytest.mark.integration
async def test_send_raw_transaction_and_get_balance(
    test_http_client_async: AsyncClient,
):
    """Test sending a raw transaction to localnet."""
    # Get a recent blockhash
    sender = Keypair()
    receiver = Keypair().pubkey()
    amount = 1000
    sender_balance_before = await _ensure_minimum_balance(test_http_client_async, sender.pubkey(), amount + 50_000)
    receiver_balance_before = await _ensure_minimum_balance(test_http_client_async, receiver, 1)
    resp = await test_http_client_async.get_latest_blockhash(Finalized)
    assert_valid_response(resp)
    recent_blockhash = resp.value.blockhash
    assert recent_blockhash is not None
    # Create transfer tx transfer lamports from stubbed sender to async_stubbed_receiver
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ixs = [
        sp.transfer(
            sp.TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=receiver,
                lamports=amount,
            )
        )
    ]
    msg = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    fee_resp = await test_http_client_async.get_fee_for_message(msg)
    assert_valid_response(fee_resp)
    assert fee_resp.value is not None
    transfer_tx = VersionedTransaction(msg, [sender])
    # Send raw transaction
    resp = await test_http_client_async.send_raw_transaction(bytes(transfer_tx))
    assert_valid_response(resp)
    # Confirm transaction
    resp = await test_http_client_async.confirm_transaction(resp.value)
    # Check balances
    resp = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(resp)
    assert resp.value == sender_balance_before - amount - fee_resp.value
    resp = await test_http_client_async.get_balance(receiver)
    assert_valid_response(resp)
    assert resp.value == receiver_balance_before + amount


@pytest.mark.integration
async def test_send_raw_transaction_and_get_balance_using_latest_blockheight(
    test_http_client_async: AsyncClient,
):
    """Test sending a raw transaction to localnet using latest blockhash."""
    # Get latest blockhash
    sender = Keypair()
    receiver = Keypair().pubkey()
    amount = 1000
    sender_balance_before = await _ensure_minimum_balance(test_http_client_async, sender.pubkey(), amount + 50_000)
    receiver_balance_before = await _ensure_minimum_balance(test_http_client_async, receiver, 1)
    resp = await test_http_client_async.get_latest_blockhash(Finalized)
    assert_valid_response(resp)
    recent_blockhash = resp.value.blockhash
    assert recent_blockhash is not None
    last_valid_block_height = resp.value.last_valid_block_height
    # Create transfer tx transfer lamports from stubbed sender to async_stubbed_receiver
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ixs = [
        sp.transfer(
            sp.TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=receiver,
                lamports=amount,
            )
        )
    ]
    msg = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    fee_resp = await test_http_client_async.get_fee_for_message(msg)
    assert_valid_response(fee_resp)
    assert fee_resp.value is not None
    transfer_tx = VersionedTransaction(msg, [sender])
    # Send raw transaction
    resp = await test_http_client_async.send_raw_transaction(
        bytes(transfer_tx),
        opts=TxOpts(
            preflight_commitment=Processed,
            last_valid_block_height=last_valid_block_height,
        ),
    )
    assert_valid_response(resp)
    # Confirm transaction
    resp = await test_http_client_async.confirm_transaction(resp.value, last_valid_block_height=last_valid_block_height)
    # Check balances
    resp = await test_http_client_async.get_balance(sender.pubkey())
    assert_valid_response(resp)
    assert resp.value == sender_balance_before - amount - fee_resp.value
    resp = await test_http_client_async.get_balance(receiver)
    assert_valid_response(resp)
    assert resp.value == receiver_balance_before + amount


@pytest.mark.integration
async def test_confirm_expired_transaction(stubbed_sender, stubbed_receiver, test_http_client_async: AsyncClient):
    """Test that RPCException is raised when trying to confirm a transaction that exceeded last valid block height."""
    # Get a recent blockhash
    resp = await test_http_client_async.get_latest_blockhash()
    recent_blockhash = resp.value.blockhash
    assert recent_blockhash is not None
    last_valid_block_height = resp.value.last_valid_block_height - 330
    # Create transfer tx transfer lamports from stubbed sender to stubbed_receiver
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    ixs = [
        sp.transfer(
            sp.TransferParams(
                from_pubkey=stubbed_sender.pubkey(),
                to_pubkey=stubbed_receiver,
                lamports=1000,
            )
        )
    ]
    msg = MessageV0.try_compile(
        payer=stubbed_sender.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    transfer_tx = VersionedTransaction(msg, [stubbed_sender])
    # Send raw transaction
    resp = await test_http_client_async.send_raw_transaction(
        bytes(transfer_tx), opts=TxOpts(skip_confirmation=True, skip_preflight=True)
    )
    assert_valid_response(resp)
    # Confirm transaction
    with pytest.raises(TransactionExpiredBlockheightExceededError) as exc_info:
        await test_http_client_async.confirm_transaction(
            resp.value, Finalized, last_valid_block_height=last_valid_block_height
        )
    err_object = exc_info.value.args[0]
    assert "block height exceeded" in err_object


@pytest.mark.integration
async def test_get_fee_for_transaction_message(stubbed_sender, stubbed_receiver, test_http_client_async: AsyncClient):
    """Test that gets a fee for a transaction using get fee for message."""
    # Get latest blockhash
    resp = await test_http_client_async.get_latest_blockhash()
    recent_blockhash = resp.value.blockhash
    assert recent_blockhash is not None
    # Create transfer tx transfer lamports from stubbed sender to stubbed_receiver
    ixs = [
        sp.transfer(
            sp.TransferParams(
                from_pubkey=stubbed_sender.pubkey(),
                to_pubkey=stubbed_receiver,
                lamports=1000,
            )
        )
    ]
    msg = MessageV0.try_compile(
        payer=stubbed_sender.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    # Get fee for transaction message
    fee_resp = await test_http_client_async.get_fee_for_message(msg)
    assert_valid_response(fee_resp)
    assert fee_resp.value is not None


@pytest.mark.integration
async def test_get_fee_for_versioned_message(
    stubbed_sender: Keypair,
    stubbed_receiver: Pubkey,
    test_http_client_async: AsyncClient,
):
    """Test that gets a fee for a transaction using get_fee_for_message."""
    # Get a recent blockhash
    resp = await test_http_client_async.get_latest_blockhash()
    recent_blockhash = resp.value.blockhash
    assert recent_blockhash is not None
    msg = MessageV0.try_compile(
        payer=stubbed_sender.pubkey(),
        instructions=[
            sp.transfer(
                sp.TransferParams(
                    from_pubkey=stubbed_sender.pubkey(),
                    to_pubkey=stubbed_receiver,
                    lamports=1000,
                )
            )
        ],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    # get fee for transaction
    fee_resp = await test_http_client_async.get_fee_for_message(msg)
    assert_valid_response(fee_resp)
    assert fee_resp.value is not None


@pytest.mark.integration
async def test_get_block_commitment(test_http_client_async: AsyncClient):
    """Test get block commitment."""
    resp = await test_http_client_async.get_block_commitment(5)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_block_time(test_http_client_async: AsyncClient):
    """Test get block time."""
    resp = await test_http_client_async.get_block_time(5)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_cluster_nodes(test_http_client_async: AsyncClient):
    """Test get cluster nodes."""
    resp = await test_http_client_async.get_cluster_nodes()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_block(test_http_client_async: AsyncClient):
    """Test get confirmed block."""
    resp = await test_http_client_async.get_block(2, commitment=Commitment.CONFIRMED)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_block_height(test_http_client_async: AsyncClient):
    """Test get height."""
    resp = await test_http_client_async.get_block_height()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_blocks(test_http_client_async: AsyncClient):
    """Test get blocks."""
    resp = await test_http_client_async.get_blocks(5, 10)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_signatures_for_address(test_http_client_async: AsyncClient):
    """Test get signatures for addresses."""
    resp = await test_http_client_async.get_signatures_for_address(VOTE_PROGRAM_ID, limit=1, commitment=Confirmed)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_epoch_info(test_http_client_async: AsyncClient):
    """Test get epoch info."""
    resp = await test_http_client_async.get_epoch_info()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_epoch_schedule(test_http_client_async: AsyncClient):
    """Test get epoch schedule."""
    resp = await test_http_client_async.get_epoch_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_latest_blockhash(test_http_client_async: AsyncClient):
    """Test get latest blockhash."""
    resp = await test_http_client_async.get_latest_blockhash(Finalized)
    assert_valid_response(resp)
    assert resp.value.blockhash is not None
    assert resp.value.last_valid_block_height is not None


@pytest.mark.integration
async def test_get_slot(test_http_client_async: AsyncClient):
    """Test get slot."""
    resp = await test_http_client_async.get_slot()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_first_available_block(test_http_client_async: AsyncClient):
    """Test get first available block."""
    resp = await test_http_client_async.get_first_available_block()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_genesis_hash(test_http_client_async: AsyncClient):
    """Test get genesis hash."""
    resp = await test_http_client_async.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_identity(test_http_client_async: AsyncClient):
    """Test get identity."""
    resp = await test_http_client_async.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_inflation_governor(test_http_client_async: AsyncClient):
    """Test get inflation governor."""
    resp = await test_http_client_async.get_inflation_governor()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_inflation_rate(test_http_client_async: AsyncClient):
    """Test get inflation rate."""
    resp = await test_http_client_async.get_inflation_rate()
    assert_valid_response(resp)


# XXX: Block not available for slot on local cluster
@pytest.mark.skip(reason="Local test validator does not provide stable reward history for getInflationReward.")
@pytest.mark.integration
async def test_get_inflation_reward(stubbed_sender, test_http_client_async: AsyncClient):
    """Test get inflation reward."""
    resp = await test_http_client_async.get_inflation_reward([stubbed_sender.pubkey()], commitment=Confirmed)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_largest_accounts(test_http_client_async: AsyncClient):
    """Test get largest accounts."""
    resp = await test_http_client_async.get_largest_accounts()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_leader_schedule(test_http_client_async: AsyncClient):
    """Test get leader schedule."""
    resp = await test_http_client_async.get_leader_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_minimum_balance_for_rent_exemption(
    test_http_client_async: AsyncClient,
):
    """Test get minimum balance for rent exemption."""
    resp = await test_http_client_async.get_minimum_balance_for_rent_exemption(50)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_slot_leader(test_http_client_async: AsyncClient):
    """Test get slot leader."""
    resp = await test_http_client_async.get_slot_leader()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_supply(test_http_client_async: AsyncClient):
    """Test get slot leader."""
    resp = await test_http_client_async.get_supply()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_token_largest_accounts(test_http_client_async: AsyncClient):
    """Test get token largest accounts."""
    resp = await test_http_client_async.get_token_largest_accounts(WRAPPED_SOL_MINT)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_token_supply(test_http_client_async: AsyncClient):
    """Test get token supply."""
    resp = await test_http_client_async.get_token_supply(WRAPPED_SOL_MINT)
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_transaction_count(test_http_client_async: AsyncClient):
    """Test get transactinon count."""
    resp = await test_http_client_async.get_transaction_count()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_version(test_http_client_async: AsyncClient):
    """Test get version."""
    resp = await test_http_client_async.get_version()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_send_rpc_request_get_version(test_http_client_async: AsyncClient):
    """Test a custom JSON-RPC request and Pydantic parser against local validator."""

    class GetVersionRequest(JsonRpcRequest):
        """Custom getVersion JSON-RPC request."""

        id: str | int = "0"
        method: str = "getVersion"

    class GetVersionResult(BaseModel):
        """Custom getVersion JSON-RPC result parser."""

        feature_set: int = Field(alias="feature-set")
        solana_core: str = Field(alias="solana-core")

    resp = await test_http_client_async.send_rpc_request(GetVersionRequest(), GetVersionResult)
    assert resp.feature_set >= 0
    assert resp.solana_core


@pytest.mark.integration
async def test_get_account_info(async_stubbed_sender, test_http_client_async: AsyncClient):
    """Test get_account_info."""
    resp = await test_http_client_async.get_account_info(async_stubbed_sender.pubkey())
    assert_valid_response(resp)
    resp = await test_http_client_async.get_account_info(async_stubbed_sender.pubkey(), encoding="jsonParsed")
    assert_valid_response(resp)
    resp = await test_http_client_async.get_account_info(
        async_stubbed_sender.pubkey(), data_slice=DataSliceOpts(offset=1, length=1)
    )
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_multiple_accounts(async_stubbed_sender, test_http_client_async: AsyncClient):
    """Test get_multiple_accounts."""
    pubkeys = [async_stubbed_sender.pubkey()] * 2
    resp = await test_http_client_async.get_multiple_accounts(pubkeys)
    assert_valid_response(resp)
    resp = await test_http_client_async.get_multiple_accounts(pubkeys, encoding="jsonParsed")
    assert_valid_response(resp)
    resp = await test_http_client_async.get_multiple_accounts(pubkeys, data_slice=DataSliceOpts(offset=1, length=1))
    assert_valid_response(resp)


@pytest.mark.integration
async def test_get_vote_accounts(test_http_client_async: AsyncClient):
    """Test get vote accounts."""
    resp = await test_http_client_async.get_vote_accounts()
    assert_valid_response(resp)


@pytest.mark.integration
async def test_rate_limiter_throttles_requests(validator_rpc_url: str):
    """Rate-limited AsyncClient should queue requests and throttle throughput.

    Strategy: create a dedicated client with rate_limit=50 req/s, fire
    500 requests concurrently via asyncio.gather, then assert the total wall
    time is at least as long as the limiter's theoretical minimum.

    With max_rate=50/s the first 50 slots are consumed immediately; each
    subsequent request must wait an additional 1/50 s = 20 ms, so the minimum
    total elapsed time for 500 requests is (500-50)/50 = 9.0 s. A 0.90
    safety factor (10% jitter tolerance) keeps the assertion resilient to
    scheduler variance while still catching a broken/missing limiter (which
    would complete in < 0.1 s on localhost).
    """
    rate_limit = 50  # requests per second
    n_requests = 500
    time_period = 1.0  # seconds (matches AsyncLimiter default)

    async with AsyncClient(endpoint=validator_rpc_url, commitment=Processed, rate_limit=rate_limit) as client:
        start = monotonic()
        responses = await asyncio.gather(*[client.get_slot() for _ in range(n_requests)])
        elapsed = monotonic() - start

    for resp in responses:
        assert_valid_response(resp)

    # Theoretical min: (n_requests - rate_limit) / rate_limit * time_period
    expected_min = (n_requests - rate_limit) / rate_limit * time_period * 0.90
    assert elapsed >= expected_min, (
        f"Rate limiter did not throttle: elapsed={elapsed:.3f}s, expected >= {expected_min:.3f}s "
        f"(rate_limit={rate_limit}/s, n_requests={n_requests})"
    )
