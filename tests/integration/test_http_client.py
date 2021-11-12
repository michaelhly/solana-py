"""Tests for the HTTP API Client."""
import pytest

import solana.system_program as sp
from solana.rpc.api import DataSliceOpt, Client
from solana.keypair import Keypair
from solana.rpc.core import RPCException
from solana.rpc.types import RPCError
from solana.transaction import Transaction
from solana.rpc.commitment import Finalized
from spl.token.constants import WRAPPED_SOL_MINT

from .utils import AIRDROP_AMOUNT, assert_valid_response


@pytest.mark.integration
def test_request_air_drop(stubbed_sender: Keypair, test_http_client: Client):
    """Test air drop to stubbed_sender."""
    resp = test_http_client.request_airdrop(stubbed_sender.public_key, AIRDROP_AMOUNT)
    assert_valid_response(resp)
    test_http_client.confirm_transaction(resp["result"])
    balance = test_http_client.get_balance(stubbed_sender.public_key)
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.integration
def test_request_air_drop_prefetched_blockhash(stubbed_sender_prefetched_blockhash, test_http_client):
    """Test air drop to stubbed_sender."""
    resp = test_http_client.request_airdrop(stubbed_sender_prefetched_blockhash.public_key, AIRDROP_AMOUNT)
    assert_valid_response(resp)
    test_http_client.confirm_transaction(resp["result"])
    balance = test_http_client.get_balance(stubbed_sender_prefetched_blockhash.public_key)
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.integration
def test_request_air_drop_cached_blockhash(stubbed_sender_cached_blockhash, test_http_client):
    """Test air drop to stubbed_sender."""
    resp = test_http_client.request_airdrop(stubbed_sender_cached_blockhash.public_key, AIRDROP_AMOUNT)
    assert_valid_response(resp)
    test_http_client.confirm_transaction(resp["result"])
    assert_valid_response(resp)
    balance = test_http_client.get_balance(stubbed_sender_cached_blockhash.public_key)
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.integration
def test_send_invalid_transaction(test_http_client):
    """Test sending an invalid transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_receiver
    with pytest.raises(RPCException) as exc_info:
        test_http_client.send_raw_transaction(b"foo")
    assert exc_info.value.args[0].keys() == RPCError.__annotations__.keys()  # pylint: disable=no-member


@pytest.mark.integration
def test_send_transaction_and_get_balance(stubbed_sender, stubbed_receiver, test_http_client):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_receiver
    transfer_tx = Transaction().add(
        sp.transfer(sp.TransferParams(from_pubkey=stubbed_sender.public_key, to_pubkey=stubbed_receiver, lamports=1000))
    )
    resp = test_http_client.send_transaction(transfer_tx, stubbed_sender)
    assert_valid_response(resp)
    # Confirm transaction
    test_http_client.confirm_transaction(resp["result"])
    # Check balances
    resp = test_http_client.get_balance(stubbed_sender.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000
    resp = test_http_client.get_balance(stubbed_receiver)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954


@pytest.mark.integration
def test_send_transaction_prefetched_blockhash(
    stubbed_sender_prefetched_blockhash, stubbed_receiver_prefetched_blockhash, test_http_client
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_receiver
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=stubbed_sender_prefetched_blockhash.public_key,
                to_pubkey=stubbed_receiver_prefetched_blockhash,
                lamports=1000,
            )
        )
    )
    recent_blockhash = test_http_client.parse_recent_blockhash(test_http_client.get_recent_blockhash(Finalized))
    resp = test_http_client.send_transaction(
        transfer_tx, stubbed_sender_prefetched_blockhash, recent_blockhash=recent_blockhash
    )
    assert_valid_response(resp)
    # Confirm transaction
    test_http_client.confirm_transaction(resp["result"])
    # Check balances
    resp = test_http_client.get_balance(stubbed_sender_prefetched_blockhash.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000
    resp = test_http_client.get_balance(stubbed_receiver_prefetched_blockhash)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954


@pytest.mark.integration
def test_send_transaction_cached_blockhash(
    stubbed_sender_cached_blockhash, stubbed_receiver_cached_blockhash, test_http_client_cached_blockhash
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer lamports from stubbed sender to stubbed_receiver
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=stubbed_sender_cached_blockhash.public_key,
                to_pubkey=stubbed_receiver_cached_blockhash,
                lamports=1000,
            )
        )
    )
    assert len(test_http_client_cached_blockhash.blockhash_cache.unused_blockhashes) == 0
    assert len(test_http_client_cached_blockhash.blockhash_cache.used_blockhashes) == 0
    resp = test_http_client_cached_blockhash.send_transaction(transfer_tx, stubbed_sender_cached_blockhash)
    # we could have got a new blockhash or not depending on network latency and luck
    assert len(test_http_client_cached_blockhash.blockhash_cache.unused_blockhashes) in (0, 1)
    assert len(test_http_client_cached_blockhash.blockhash_cache.used_blockhashes) == 1
    assert_valid_response(resp)
    # Confirm transaction
    test_http_client_cached_blockhash.confirm_transaction(resp["result"])
    # Check balances
    resp = test_http_client_cached_blockhash.get_balance(stubbed_sender_cached_blockhash.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999994000

    # Second transaction
    transfer_tx = Transaction().add(
        sp.transfer(
            sp.TransferParams(
                from_pubkey=stubbed_sender_cached_blockhash.public_key,
                to_pubkey=stubbed_receiver_cached_blockhash,
                lamports=2000,
            )
        )
    )
    resp = test_http_client_cached_blockhash.get_balance(stubbed_receiver_cached_blockhash)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 954
    resp = test_http_client_cached_blockhash.send_transaction(transfer_tx, stubbed_sender_cached_blockhash)
    # we could have got a new blockhash or not depending on network latency and luck
    assert len(test_http_client_cached_blockhash.blockhash_cache.unused_blockhashes) in (0, 1)
    assert len(test_http_client_cached_blockhash.blockhash_cache.used_blockhashes) in (1, 2)
    assert_valid_response(resp)
    # Confirm transaction
    test_http_client_cached_blockhash.confirm_transaction(resp["result"])
    # Check balances
    resp = test_http_client_cached_blockhash.get_balance(stubbed_sender_cached_blockhash.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999987000
    assert len(test_http_client_cached_blockhash.blockhash_cache.unused_blockhashes) == 1
    assert len(test_http_client_cached_blockhash.blockhash_cache.used_blockhashes) == 1


@pytest.mark.integration
def test_send_raw_transaction_and_get_balance(stubbed_sender, stubbed_receiver, test_http_client):
    """Test sending a raw transaction to localnet."""
    # Get a recent blockhash
    resp = test_http_client.get_recent_blockhash(Finalized)
    assert_valid_response(resp)
    recent_blockhash = resp["result"]["value"]["blockhash"]
    # Create transfer tx transfer lamports from stubbed sender to stubbed_receiver
    transfer_tx = Transaction(recent_blockhash=recent_blockhash).add(
        sp.transfer(sp.TransferParams(from_pubkey=stubbed_sender.public_key, to_pubkey=stubbed_receiver, lamports=1000))
    )
    # Sign transaction
    transfer_tx.sign(stubbed_sender)
    # Send raw transaction
    resp = test_http_client.send_raw_transaction(transfer_tx.serialize())
    assert_valid_response(resp)
    # Confirm transaction
    test_http_client.confirm_transaction(resp["result"])
    # Check balances
    resp = test_http_client.get_balance(stubbed_sender.public_key)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 9999988000
    resp = test_http_client.get_balance(stubbed_receiver)
    assert_valid_response(resp)
    assert resp["result"]["value"] == 1954


@pytest.mark.integration
def test_confirm_bad_signature(test_http_client: Client) -> None:
    """Test that RPCException is raised when trying to confirm an invalid signature."""
    with pytest.raises(RPCException) as exc_info:
        test_http_client.confirm_transaction("foo")
    err_object = exc_info.value.args[0]
    assert err_object == {"code": -32602, "message": "Invalid param: WrongSize"}


@pytest.mark.integration
def test_get_block_commitment(test_http_client):
    """Test get block commitment."""
    resp = test_http_client.get_block_commitment(5)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_block_time(test_http_client):
    """Test get block time."""
    resp = test_http_client.get_block_time(5)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_cluster_nodes(test_http_client):
    """Test get cluster nodes."""
    resp = test_http_client.get_cluster_nodes()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_block(test_http_client):
    """Test get confirmed block."""
    resp = test_http_client.get_confirmed_block(1)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_block_with_encoding(test_http_client):
    """Test get confrimed block with encoding."""
    resp = test_http_client.get_confirmed_block(1, encoding="base64")
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_blocks(test_http_client):
    """Test get confirmed blocks."""
    resp = test_http_client.get_confirmed_blocks(5, 10)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_confirmed_signature_for_address2(test_http_client):
    """Test get confirmed signature for address2."""
    resp = test_http_client.get_confirmed_signature_for_address2("Vote111111111111111111111111111111111111111", limit=1)
    assert_valid_response(resp)


# TODO(michael): This RPC call is only available in solana-core v1.7 or newer.
# @pytest.mark.integration
# def test_get_signatures_for_address(test_http_client):
#     """Test get signatures for addresses."""
#     resp = test_http_client.get_signatures_for_address("Vote111111111111111111111111111111111111111", limit=1)
#     assert_valid_response(resp)


@pytest.mark.integration
def test_get_epoch_info(test_http_client):
    """Test get epoch info."""
    resp = test_http_client.get_epoch_info()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_epoch_schedule(test_http_client):
    """Test get epoch schedule."""
    resp = test_http_client.get_epoch_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_fee_calculator_for_blockhash(test_http_client):
    """Test get fee calculator for blockhash."""
    resp = test_http_client.get_recent_blockhash(Finalized)
    assert_valid_response(resp)
    resp = test_http_client.get_fee_calculator_for_blockhash(resp["result"]["value"]["blockhash"])
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_slot(test_http_client):
    """Test get slot."""
    resp = test_http_client.get_slot()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_fees(test_http_client):
    """Test get fees."""
    resp = test_http_client.get_fees()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_first_available_block(test_http_client):
    """Test get first available block."""
    resp = test_http_client.get_first_available_block()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_genesis_hash(test_http_client):
    """Test get genesis hash."""
    resp = test_http_client.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_identity(test_http_client):
    """Test get identity."""
    resp = test_http_client.get_genesis_hash()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_inflation_governor(test_http_client):
    """Test get inflation governor."""
    resp = test_http_client.get_inflation_governor()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_inflation_rate(test_http_client):
    """Test get inflation rate."""
    resp = test_http_client.get_inflation_rate()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_largest_accounts(test_http_client):
    """Test get largest accounts."""
    resp = test_http_client.get_largest_accounts()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_leader_schedule(test_http_client):
    """Test get leader schedule."""
    resp = test_http_client.get_leader_schedule()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_minimum_balance_for_rent_exemption(test_http_client):
    """Test get minimum balance for rent exemption."""
    resp = test_http_client.get_minimum_balance_for_rent_exemption(50)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_slot_leader(test_http_client):
    """Test get slot leader."""
    resp = test_http_client.get_slot_leader()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_supply(test_http_client):
    """Test get slot leader."""
    resp = test_http_client.get_supply()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_transaction_count(test_http_client):
    """Test get transactinon count."""
    resp = test_http_client.get_transaction_count()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_version(test_http_client):
    """Test get version."""
    resp = test_http_client.get_version()
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_account_info(stubbed_sender, test_http_client):
    """Test get_account_info."""
    resp = test_http_client.get_account_info(stubbed_sender.public_key)
    assert_valid_response(resp)
    resp = test_http_client.get_account_info(stubbed_sender.public_key, encoding="jsonParsed")
    assert_valid_response(resp)
    resp = test_http_client.get_account_info(stubbed_sender.public_key, data_slice=DataSliceOpt(1, 1))
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_multiple_accounts(stubbed_sender, test_http_client):
    """Test get_multiple_accounts."""
    pubkeys = [stubbed_sender.public_key] * 2
    resp = test_http_client.get_multiple_accounts(pubkeys)
    assert_valid_response(resp)
    resp = test_http_client.get_multiple_accounts(pubkeys, encoding="jsonParsed")
    assert_valid_response(resp)
    resp = test_http_client.get_multiple_accounts(pubkeys, data_slice=DataSliceOpt(1, 1))
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_token_largest_accounts(test_http_client):
    """Test get token largest accounts."""
    resp = test_http_client.get_token_largest_accounts(WRAPPED_SOL_MINT)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_token_supply(test_http_client):
    """Test get token supply."""
    resp = test_http_client.get_token_supply(WRAPPED_SOL_MINT)
    assert_valid_response(resp)


@pytest.mark.integration
def test_get_vote_accounts(test_http_client):
    """Test get vote accounts."""
    resp = test_http_client.get_vote_accounts()
    assert_valid_response(resp)
