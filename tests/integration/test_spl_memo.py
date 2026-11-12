"""Tests for the Memo program."""

import pytest
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.transaction_status import ParsedInstruction, UiTransaction

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Finalized
from solana.spl.memo import MEMO_PROGRAM_ID, AddMemoParams, add_memo

from ..utils import AIRDROP_AMOUNT, assert_valid_response


@pytest.mark.integration
async def test_send_memo_in_transaction(test_http_client_async: AsyncClient):
    """Test sending a signed memo instruction to localnet."""
    sender = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(sender.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(airdrop_resp)
    await test_http_client_async.confirm_transaction(airdrop_resp.value)
    raw_message = "test"
    ix = add_memo(AddMemoParams(memo=raw_message, signers=(sender.pubkey(),)))
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    msg = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    resp = await test_http_client_async.send_transaction(VersionedTransaction(msg, [sender]))
    assert_valid_response(resp)
    txn_id = resp.value
    # Txn needs to be finalized in order to parse the logs.
    await test_http_client_async.confirm_transaction(txn_id, commitment=Finalized)
    resp2_val = (
        await test_http_client_async.get_transaction(
            txn_id,
            commitment=Finalized,
            encoding="jsonParsed",
            max_supported_transaction_version=0,
        )
    ).value
    assert resp2_val is not None
    resp2_transaction = resp2_val.transaction
    meta = resp2_transaction.meta
    assert meta is not None
    messages = meta.log_messages
    assert messages is not None
    assert messages[1:5] == [
        "Program log: Signed by:",
        f"Program log: {sender.pubkey()}",
        f"Program log: Memo (len {len(raw_message)})",
        f"Program log: {raw_message}",
    ]
    assert isinstance(resp2_transaction.transaction, UiTransaction)
    ixn = resp2_transaction.transaction.message.instructions[0]
    assert isinstance(ixn, ParsedInstruction)
    assert ixn.parsed == raw_message
    assert ixn.program_id == MEMO_PROGRAM_ID
