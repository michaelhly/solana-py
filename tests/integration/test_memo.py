"""Tests for the Memo program."""
from json import loads
import pytest

from solana.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.commitment import Finalized
from solana.transaction import Transaction
from spl.memo.constants import MEMO_PROGRAM_ID
from spl.memo.instructions import MemoParams, create_memo

from .utils import AIRDROP_AMOUNT, assert_valid_response


@pytest.mark.integration
def test_send_memo_in_transaction(stubbed_sender: Keypair, test_http_client: Client):
    """Test sending a memo instruction to localnet."""
    airdrop_resp = test_http_client.request_airdrop(stubbed_sender.public_key, AIRDROP_AMOUNT)
    assert_valid_response(airdrop_resp)
    test_http_client.confirm_transaction(airdrop_resp.value)
    raw_message = "test"
    message = bytes(raw_message, encoding="utf8")
    # Create memo params
    memo_params = MemoParams(
        program_id=MEMO_PROGRAM_ID,
        signer=stubbed_sender.public_key,
        message=message,
    )
    # Create memo instruction
    memo_ix = create_memo(memo_params)
    # Create transfer tx to add memo to transaction from stubbed sender
    transfer_tx = Transaction().add(memo_ix)
    resp = test_http_client.send_transaction(transfer_tx, stubbed_sender)
    assert_valid_response(resp)
    txn_id = resp.value
    # Txn needs to be finalized in order to parse the logs.
    test_http_client.confirm_transaction(txn_id, commitment=Finalized)
    resp2 = test_http_client.get_transaction(txn_id, commitment=Finalized, encoding="jsonParsed")
    resp2_val = resp2.value
    assert resp2_val is not None
    resp2_transaction = resp2_val.transaction
    log_message = resp2_transaction.meta.log_messages[2].split('"')
    assert log_message[1] == raw_message
    ixn = resp2_transaction.transaction.message.instructions[0]
    assert loads(ixn.parsed) == raw_message
    assert ixn.program_id == MEMO_PROGRAM_ID.to_solders()
