"""Tests for the Memo program."""
import pytest
from solders.keypair import Keypair
from solders.transaction_status import ParsedInstruction
from spl.compute_budget.constants import COMPUTE_BUDGET_PROGRAM_ID
from spl.compute_budget.instructions import (
    RequestHeapFrameParams,
    SetComputeUnitLimitParams,
    SetComputeUnitPriceParams,
    request_heap_frame,
    set_compute_unit_limit,
    set_compute_unit_price,
)
from solana.rpc.api import Client
from solana.rpc.commitment import Finalized
from solana.transaction import Transaction

from ..utils import AIRDROP_AMOUNT, assert_valid_response


@pytest.mark.integration
def test_request_heap_frame(stubbed_sender: Keypair, test_http_client: Client):
    """Test sending a memo instruction to localnet."""
    airdrop_resp = test_http_client.request_airdrop(stubbed_sender.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(airdrop_resp)
    test_http_client.confirm_transaction(airdrop_resp.value)
    # Create tx to request heap frame for stubbed sender
    heap_frame_params = RequestHeapFrameParams(bytes=32_000 * 1024)
    tx = Transaction().add(request_heap_frame(heap_frame_params))
    resp = test_http_client.send_transaction(tx, stubbed_sender)
    assert_valid_response(resp)
    txn_id = resp.value
    # Txn needs to be finalized in order to parse the logs.
    test_http_client.confirm_transaction(txn_id, commitment=Finalized)
    resp2_val = test_http_client.get_transaction(txn_id, commitment=Finalized, encoding="jsonParsed").value
    assert resp2_val is not None
    resp2_transaction = resp2_val.transaction
    meta = resp2_transaction.meta
    assert meta is not None
    messages = meta.log_messages
    assert messages is not None
    ixn = resp2_transaction.transaction.message.instructions[0]
    assert isinstance(ixn, ParsedInstruction)
    print(ixn.parsed)
    assert ixn.program_id == COMPUTE_BUDGET_PROGRAM_ID


@pytest.mark.integration
def test_set_compute_unit_limit(stubbed_sender: Keypair, test_http_client: Client):
    """Test sending a memo instruction to localnet."""
    airdrop_resp = test_http_client.request_airdrop(stubbed_sender.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(airdrop_resp)
    test_http_client.confirm_transaction(airdrop_resp.value)
    # Create tx to set compute unit limit for stubbed sender
    compute_unit_limit_params = SetComputeUnitLimitParams(units=150_000)
    tx = Transaction().add(set_compute_unit_limit(compute_unit_limit_params))
    resp = test_http_client.send_transaction(tx, stubbed_sender)
    assert_valid_response(resp)
    txn_id = resp.value
    # Txn needs to be finalized in order to parse the logs.
    test_http_client.confirm_transaction(txn_id, commitment=Finalized)
    resp2_val = test_http_client.get_transaction(txn_id, commitment=Finalized, encoding="jsonParsed").value
    assert resp2_val is not None
    resp2_transaction = resp2_val.transaction
    meta = resp2_transaction.meta
    assert meta is not None
    messages = meta.log_messages
    assert messages is not None
    ixn = resp2_transaction.transaction.message.instructions[0]
    assert isinstance(ixn, ParsedInstruction)
    print(ixn.parsed)
    assert ixn.program_id == COMPUTE_BUDGET_PROGRAM_ID


@pytest.mark.integration
def test_set_compute_unit_price(stubbed_sender: Keypair, test_http_client: Client):
    """Test sending a memo instruction to localnet."""
    airdrop_resp = test_http_client.request_airdrop(stubbed_sender.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(airdrop_resp)
    test_http_client.confirm_transaction(airdrop_resp.value)
    # Create tx to set compute unit price for stubbed sender
    compute_unit_price_params = SetComputeUnitPriceParams(micro_lamports=1500)
    tx = Transaction().add(set_compute_unit_price(compute_unit_price_params))
    resp = test_http_client.send_transaction(tx, stubbed_sender)
    assert_valid_response(resp)
    txn_id = resp.value
    # Txn needs to be finalized in order to parse the logs.
    test_http_client.confirm_transaction(txn_id, commitment=Finalized)
    resp2_val = test_http_client.get_transaction(txn_id, commitment=Finalized, encoding="jsonParsed").value
    assert resp2_val is not None
    resp2_transaction = resp2_val.transaction
    meta = resp2_transaction.meta
    assert meta is not None
    messages = meta.log_messages
    assert messages is not None
    ixn = resp2_transaction.transaction.message.instructions[0]
    assert isinstance(ixn, ParsedInstruction)
    print(ixn.parsed)
    assert ixn.program_id == COMPUTE_BUDGET_PROGRAM_ID

