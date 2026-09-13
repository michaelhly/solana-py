"""Tests for the Websocket Client."""

import asyncio
from collections.abc import AsyncGenerator

import asyncstdlib
import pytest
from solders import system_program as sp
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.rpc.config import (
    RpcTransactionLogsFilter,
    RpcTransactionLogsFilterMentions,
)
from solders.rpc.responses import (
    AccountNotification,
    LogsNotification,
    BlockNotification,
    ProgramNotification,
    RootNotification,
    SignatureNotification,
    SlotNotification,
    SlotUpdateNotification,
    VoteNotification,
)

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Finalized
from solana.rpc.models import TxOpts
from solana.rpc.websocket_api import SolanaWsClient
from solders.transaction import VersionedTransaction

from ..utils import AIRDROP_AMOUNT


async def _send_transfer(client: AsyncClient, sender: Keypair, recipient: Pubkey, lamports: int) -> str:
    blockhash = (await client.get_latest_blockhash()).value.blockhash
    message = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=[
            sp.transfer(sp.TransferParams(from_pubkey=sender.pubkey(), to_pubkey=recipient, lamports=lamports))
        ],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    response = await client.send_transaction(
        VersionedTransaction(message, [sender]),
        opts=TxOpts(skip_preflight=True),
    )
    return str(response.value)


@pytest.fixture
async def websocket(
    test_http_client_async: AsyncClient,
    validator_ws_url: str,
) -> AsyncGenerator[SolanaWsClient, None]:
    """Websocket connection to the local test validator."""
    async with SolanaWsClient(uri=validator_ws_url) as client:
        yield client


@pytest.fixture
async def multiple_subscriptions(
    stubbed_sender_for_websockets: Keypair, websocket: SolanaWsClient
) -> AsyncGenerator[None, None]:
    """Setup multiple subscriptions."""
    logs = await websocket.logs_subscribe()
    account = await websocket.account_subscribe(pubkey=stubbed_sender_for_websockets.pubkey())
    yield
    await websocket.unsubscribe(logs)
    await websocket.unsubscribe(account)


@pytest.fixture
async def account_subscribed(
    stubbed_sender_for_websockets: Keypair, websocket: SolanaWsClient
) -> AsyncGenerator[Pubkey, None]:
    """Setup account subscription."""
    recipient = Keypair()
    subscription = await websocket.account_subscribe(
        pubkey=recipient.pubkey(),
        commitment=Finalized,
        encoding="base64",
    )
    yield recipient.pubkey()
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def logs_subscribed(
    stubbed_sender_for_websockets: Keypair, websocket: SolanaWsClient
) -> AsyncGenerator[None, None]:
    """Setup logs subscription."""
    subscription = await websocket.logs_subscribe()
    yield
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def logs_subscribed_mentions_filter(
    stubbed_sender_for_websockets: Keypair, websocket: SolanaWsClient
) -> AsyncGenerator[tuple[Pubkey, Pubkey], None]:
    """Setup logs subscription with a mentions filter."""
    recipient = Keypair().pubkey()
    unrelated = Keypair().pubkey()
    subscription = await websocket.logs_subscribe(filter_=RpcTransactionLogsFilterMentions(recipient))
    yield recipient, unrelated
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def block_subscribed(
    websocket: SolanaWsClient,
) -> AsyncGenerator[None, None]:
    """Setup block subscription."""
    subscription = await websocket.block_subscribe()
    yield
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def program_subscribed(
    websocket: SolanaWsClient, test_http_client_async: AsyncClient
) -> AsyncGenerator[tuple[Keypair, Keypair], None]:
    """Setup program subscription."""
    program = Keypair()
    owned = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(owned.pubkey(), AIRDROP_AMOUNT)
    await test_http_client_async.confirm_transaction(airdrop_resp.value)
    subscription = await websocket.program_subscribe(program_id=program.pubkey())
    yield program, owned
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def signature_subscribed(
    websocket: SolanaWsClient, test_http_client_async: AsyncClient
) -> AsyncGenerator[None, None]:
    """Setup signature subscription."""
    recipient = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(recipient.pubkey(), AIRDROP_AMOUNT)
    await websocket.signature_subscribe(signature=airdrop_resp.value, commitment=Finalized)
    # Signature subscriptions are one-shot: the server cancels them after the
    # notification, so no explicit unsubscribe is possible here.
    yield


@pytest.fixture
async def slot_subscribed(
    websocket: SolanaWsClient,
) -> AsyncGenerator[None, None]:
    """Setup slot subscription."""
    subscription = await websocket.slot_subscribe()
    yield
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def slots_updates_subscribed(
    websocket: SolanaWsClient,
) -> AsyncGenerator[None, None]:
    """Setup slots updates subscription."""
    subscription = await websocket.slots_updates_subscribe()
    yield
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def root_subscribed(
    websocket: SolanaWsClient,
) -> AsyncGenerator[None, None]:
    """Setup root subscription."""
    subscription = await websocket.root_subscribe()
    yield
    await websocket.unsubscribe(subscription)


@pytest.fixture
async def vote_subscribed(
    websocket: SolanaWsClient,
) -> AsyncGenerator[None, None]:
    """Setup vote subscription."""
    subscription = await websocket.vote_subscribe()
    yield
    await websocket.unsubscribe(subscription)


@pytest.mark.integration
async def test_multiple_subscriptions(
    stubbed_sender_for_websockets: Keypair,
    test_http_client_async: AsyncClient,
    multiple_subscriptions: None,
    websocket: SolanaWsClient,
):
    """Test subscribing to multiple feeds."""
    airdrop_resp = await test_http_client_async.request_airdrop(stubbed_sender_for_websockets.pubkey(), AIRDROP_AMOUNT)
    account_lamports = None
    logs_seen = False
    async for message in websocket:
        if isinstance(message, AccountNotification):
            account_lamports = message.result.value.lamports
        elif isinstance(message, LogsNotification):
            logs_seen = "Program 11111111111111111111111111111111 invoke [1]" in message.result.value.logs
        else:
            continue
        # Notifications can arrive in either order, and account subscriptions
        # may emit an initial state before the airdrop is processed.
        if account_lamports == AIRDROP_AMOUNT and logs_seen:
            break

    assert account_lamports == AIRDROP_AMOUNT
    assert logs_seen
    await test_http_client_async.confirm_transaction(airdrop_resp.value, Finalized)
    balance = await test_http_client_async.get_balance(stubbed_sender_for_websockets.pubkey(), Finalized)
    assert balance.value == AIRDROP_AMOUNT


@pytest.mark.integration
async def test_account_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClient,
    account_subscribed: Pubkey,
):
    """Test account subscription."""
    await test_http_client_async.request_airdrop(account_subscribed, AIRDROP_AMOUNT)
    async for msg in websocket:
        if not isinstance(msg, AccountNotification):
            continue
        assert msg.result is not None
        if msg.result.value.lamports == AIRDROP_AMOUNT:
            assert msg.result.value.owner is not None
            break
    else:
        raise AssertionError("WebSocket closed before receiving the account update")


@pytest.mark.integration
async def test_logs_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClient,
    logs_subscribed: None,
):
    """Test logs subscription."""
    recipient = Keypair().pubkey()
    await test_http_client_async.request_airdrop(recipient, AIRDROP_AMOUNT)
    msg = await websocket.recv()
    assert isinstance(msg, LogsNotification)
    assert msg.result.value.logs[0] == "Program 11111111111111111111111111111111 invoke [1]"


@pytest.mark.integration
async def test_logs_subscribe_mentions_filter(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClient,
    logs_subscribed_mentions_filter: tuple[Pubkey, Pubkey],
):
    """Test logs subscription with a mentions filter."""
    recipient, unrelated = logs_subscribed_mentions_filter
    matching_airdrop = await test_http_client_async.request_airdrop(recipient, AIRDROP_AMOUNT)
    unrelated_airdrop = await test_http_client_async.request_airdrop(unrelated, AIRDROP_AMOUNT)
    async for msg in websocket:
        if not isinstance(msg, LogsNotification):
            continue
        assert msg.result is not None
        assert str(msg.result.value.signature) == str(matching_airdrop.value)
        assert str(msg.result.value.signature) != str(unrelated_airdrop.value)
        assert "Program 11111111111111111111111111111111 invoke [1]" in msg.result.value.logs
        break
    else:
        raise AssertionError("WebSocket closed before receiving filtered logs")


@pytest.mark.integration
async def test_logs_subscribe_filter_all(test_http_client_async: AsyncClient, websocket: SolanaWsClient):
    """The ``all`` filter delivers both successful and failed transactions."""
    sender, recipient = Keypair(), Keypair().pubkey()
    subscription = await websocket.logs_subscribe(filter_=RpcTransactionLogsFilter.All)
    try:
        await test_http_client_async.request_airdrop(sender.pubkey(), AIRDROP_AMOUNT)
        success = await _send_transfer(test_http_client_async, sender, recipient, 1)
        failure = await _send_transfer(test_http_client_async, sender, recipient, AIRDROP_AMOUNT * 100)
        seen = set()
        async for message in websocket:
            if isinstance(message, LogsNotification):
                seen.add(str(message.result.value.signature))
                if success in seen and failure in seen:
                    break
        assert success in seen
        assert failure in seen
    finally:
        await websocket.unsubscribe(subscription)


@pytest.mark.integration
async def test_logs_subscribe_all_with_votes_receives_vote_log(
    websocket: SolanaWsClient,
):
    """The allWithVotes filter includes validator vote transactions."""
    subscription = await websocket.logs_subscribe(filter_=RpcTransactionLogsFilter.AllWithVotes)
    try:
        async with asyncio.timeout(120):
            async for message in websocket:
                if isinstance(message, LogsNotification) and any(
                    "Vote111111111111111111111111111111111111111" in log for log in message.result.value.logs
                ):
                    return
        raise AssertionError("No vote transaction log received within 120 seconds")
    finally:
        await websocket.unsubscribe(subscription)


@pytest.mark.integration
@pytest.mark.skip(reason="Agave 4.0 has a known RPC blockSubscribe flag issue; re-enable after upstream fix.")
async def test_block_subscribe(
    websocket: SolanaWsClient,
    block_subscribed: None,
):
    """Test block subscription."""
    # NOTE: Keep this test force-skipped until Agave fixes blockSubscribe behavior.
    msg = await websocket.recv()
    assert isinstance(msg, BlockNotification)
    assert msg.result.value.slot >= 0


@pytest.mark.integration
async def test_program_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClient,
    program_subscribed: tuple[Keypair, Keypair],
):
    """Test program subscription."""
    program, owned = program_subscribed
    ixs = [sp.assign(sp.AssignParams(pubkey=owned.pubkey(), owner=program.pubkey()))]
    blockhash = (await test_http_client_async.get_latest_blockhash()).value.blockhash
    msg = MessageV0.try_compile(
        payer=owned.pubkey(),
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )
    transaction = VersionedTransaction(msg, [owned])
    await test_http_client_async.send_transaction(transaction)
    msg = await websocket.recv()
    assert isinstance(msg, ProgramNotification)
    assert msg.result.value.pubkey == owned.pubkey()


@pytest.mark.integration
async def test_signature_subscribe(
    websocket: SolanaWsClient,
    signature_subscribed: None,
):
    """Test signature subscription."""
    msg = await websocket.recv()
    assert isinstance(msg, SignatureNotification)
    assert msg.result.value.err is None


@pytest.mark.integration
async def test_slot_subscribe(
    websocket: SolanaWsClient,
    slot_subscribed: None,
):
    """Test slot subscription."""
    msg = await websocket.recv()
    assert isinstance(msg, SlotNotification)
    assert msg.result.root >= 0


@pytest.mark.integration
async def test_slots_updates_subscribe(
    websocket: SolanaWsClient,
    slots_updates_subscribed: None,
):
    """Test slots updates subscription."""
    async for idx, resp in asyncstdlib.enumerate(websocket):
        msg = resp
        assert isinstance(msg, SlotUpdateNotification)
        assert msg.result.slot > 0
        if idx == 40:
            break


@pytest.mark.integration
async def test_root_subscribe(
    websocket: SolanaWsClient,
    root_subscribed: None,
):
    """Test root subscription."""
    msg = await websocket.recv()
    assert isinstance(msg, RootNotification)
    assert msg.result >= 0


@pytest.mark.integration
async def test_vote_subscribe(
    websocket: SolanaWsClient,
    vote_subscribed: None,
):
    """Test vote subscription."""
    msg = await websocket.recv()
    assert isinstance(msg, VoteNotification)
    assert msg.result.slots
