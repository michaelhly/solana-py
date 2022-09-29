"""Tests for the Memo program."""
import pytest
from solders.signature import Signature

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
    test_http_client.confirm_transaction(Signature.from_string(airdrop_resp["result"]))
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
    txn_id = resp["result"]
    # Txn needs to be finalized in order to parse the logs.
    test_http_client.confirm_transaction(Signature.from_string(txn_id), commitment=Finalized)
    resp2 = test_http_client.get_transaction(Signature.from_string(txn_id), commitment=Finalized, encoding="jsonParsed")
    log_message = resp2["result"]["meta"]["logMessages"][2].split('"')
    assert log_message[1] == raw_message
    assert resp2["result"]["transaction"]["message"]["instructions"][0]["parsed"] == raw_message
    assert resp2["result"]["transaction"]["message"]["instructions"][0]["programId"] == str(MEMO_PROGRAM_ID)
