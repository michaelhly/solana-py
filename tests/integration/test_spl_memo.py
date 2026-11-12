"""Tests for the Memo program."""

import pytest
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.transaction_status import ParsedInstruction, UiTransaction

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Finalized
from solana.spl.memo import MEMO_V1_PROGRAM_ID, MEMO_V3_PROGRAM_ID, MEMO_V4_PROGRAM_ID, AddMemoParams, add_memo

from ..utils import AIRDROP_AMOUNT, assert_valid_response


async def _send_memo(client: AsyncClient, sender: Keypair, ix: Instruction):
    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    return await client.send_transaction(VersionedTransaction(msg, [sender]))


def _expected_program_logs(program_id: Pubkey, signer: Pubkey, memo: str, with_signer: bool) -> list[str]:
    """Memo program log lines (without the invoke/consumed/success framing) for each program version."""
    if program_id == MEMO_V1_PROGRAM_ID:
        return []
    if program_id == MEMO_V3_PROGRAM_ID:
        signed = [f"Program log: Signed by {signer}"] if with_signer else []
        return [*signed, f'Program log: Memo (len {len(memo)}): "{memo}"']
    signed = ["Program log: Signed by:", f"Program log: {signer}"] if with_signer else []
    return [*signed, f"Program log: Memo (len {len(memo)})", f"Program log: {memo}"]


@pytest.mark.integration
@pytest.mark.parametrize(
    ("program_id", "with_signer"),
    [
        pytest.param(MEMO_V1_PROGRAM_ID, False, id="v1-no_signer"),
        pytest.param(MEMO_V3_PROGRAM_ID, False, id="v3-no_signer"),
        pytest.param(MEMO_V3_PROGRAM_ID, True, id="v3-signer"),
        pytest.param(MEMO_V4_PROGRAM_ID, False, id="v4-no_signer"),
        pytest.param(MEMO_V4_PROGRAM_ID, True, id="v4-signer"),
    ],
)
async def test_send_memo_in_transaction(test_http_client_async: AsyncClient, program_id: Pubkey, with_signer: bool):
    """Send a memo to every Memo program version; the instruction data is the same, the logs are not."""
    sender = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(sender.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(airdrop_resp)
    await test_http_client_async.confirm_transaction(airdrop_resp.value)
    raw_message = "test"
    signers = (sender.pubkey(),) if with_signer else ()
    ix = add_memo(AddMemoParams(memo=raw_message, signers=signers, program_id=program_id))

    resp = await _send_memo(test_http_client_async, sender, ix)
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
    assert messages[1:-2] == _expected_program_logs(program_id, sender.pubkey(), raw_message, with_signer)
    assert isinstance(resp2_transaction.transaction, UiTransaction)
    ixn = resp2_transaction.transaction.message.instructions[0]
    assert isinstance(ixn, ParsedInstruction)
    assert ixn.parsed == raw_message
    assert ixn.program_id == program_id
