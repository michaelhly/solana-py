# pylint: disable=unused-argument,redefined-outer-name
"""Tests for the Websocket Client."""
from typing import List, Tuple

import asyncstdlib
import pytest
from solders.rpc.requests import (
    AccountSubscribe,
    AccountUnsubscribe,
    LogsSubscribe,
    LogsUnsubscribe,
    Body,
)
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.rpc.config import RpcTransactionLogsFilter, RpcTransactionLogsFilterMentions
from solders.signature import Signature

from solana import system_program as sp
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Finalized
from solana.rpc.websocket_api import SolanaWsClientProtocol, connect
from solana.transaction import Transaction

from .utils import AIRDROP_AMOUNT


@pytest.fixture
async def websocket(test_http_client_async: AsyncClient) -> SolanaWsClientProtocol:
    """Websocket connection."""
    async with connect() as client:
        yield client


@pytest.fixture
async def multiple_subscriptions(stubbed_sender: Keypair, websocket: SolanaWsClientProtocol) -> List[Body]:
    """Setup multiple subscriptions."""
    reqs = [
        LogsSubscribe(filter_=RpcTransactionLogsFilter.All, id=websocket.increment_counter_and_get_id()),
        AccountSubscribe(stubbed_sender.public_key.to_solders(), id=websocket.increment_counter_and_get_id()),
    ]
    await websocket.send_data(reqs)  # None
    first_resp = await websocket.recv()
    logs_subscription_id, account_subscription_id = [resp.result for resp in first_resp]
    yield reqs
    unsubscribe_reqs = [
        LogsUnsubscribe(logs_subscription_id, websocket.increment_counter_and_get_id()),
        AccountUnsubscribe(account_subscription_id, websocket.increment_counter_and_get_id()),
    ]
    await websocket.send_data(unsubscribe_reqs)


@pytest.fixture
async def account_subscribed(stubbed_sender: Keypair, websocket: SolanaWsClientProtocol) -> PublicKey:
    """Setup account subscription."""
    recipient = Keypair()
    await websocket.account_subscribe(recipient.public_key)
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield recipient.public_key
    await websocket.account_unsubscribe(subscription_id)


@pytest.fixture
async def logs_subscribed(stubbed_sender: Keypair, websocket: SolanaWsClientProtocol) -> None:
    """Setup logs subscription."""
    await websocket.logs_subscribe()
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.logs_unsubscribe(subscription_id)


@pytest.fixture
async def logs_subscribed_mentions_filter(stubbed_sender: Keypair, websocket: SolanaWsClientProtocol) -> None:
    """Setup logs subscription with a mentions filter."""
    await websocket.logs_subscribe(RpcTransactionLogsFilterMentions(SYS_PROGRAM_ID))
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.logs_unsubscribe(subscription_id)


@pytest.fixture
async def program_subscribed(
    websocket: SolanaWsClientProtocol, test_http_client_async: AsyncClient
) -> Tuple[Keypair, Keypair]:
    """Setup program subscription."""
    program = Keypair()
    owned = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(owned.public_key, AIRDROP_AMOUNT)
    await test_http_client_async.confirm_transaction(Signature.from_string(airdrop_resp["result"]))
    await websocket.program_subscribe(program.public_key)
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield program, owned
    await websocket.program_unsubscribe(subscription_id)


@pytest.fixture
async def signature_subscribed(
    websocket: SolanaWsClientProtocol, test_http_client_async: AsyncClient
) -> Tuple[Keypair, Keypair]:
    """Setup signature subscription."""
    recipient = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(recipient.public_key, AIRDROP_AMOUNT)
    await websocket.signature_subscribe(Signature.from_string(airdrop_resp["result"]))
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.signature_unsubscribe(subscription_id)


@pytest.fixture
async def slot_subscribed(websocket: SolanaWsClientProtocol) -> None:
    """Setup slot subscription."""
    await websocket.slot_subscribe()
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.slot_unsubscribe(subscription_id)


@pytest.fixture
async def slots_updates_subscribed(websocket: SolanaWsClientProtocol) -> None:
    """Setup slots updates subscription."""
    await websocket.slots_updates_subscribe()
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.slots_updates_unsubscribe(subscription_id)


@pytest.fixture
async def root_subscribed(websocket: SolanaWsClientProtocol) -> None:
    """Setup root subscription."""
    await websocket.root_subscribe()
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.root_unsubscribe(subscription_id)


@pytest.fixture
async def vote_subscribed(websocket: SolanaWsClientProtocol) -> None:
    """Setup vote subscription."""
    await websocket.vote_subscribe()
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.vote_unsubscribe(subscription_id)


@pytest.mark.integration
async def test_multiple_subscriptions(
    stubbed_sender: Keypair,
    test_http_client_async: AsyncClient,
    multiple_subscriptions: List[Body],
    websocket: SolanaWsClientProtocol,
):
    """Test subscribing to multiple feeds."""
    await test_http_client_async.request_airdrop(stubbed_sender.public_key, AIRDROP_AMOUNT)
    async for idx, message in asyncstdlib.enumerate(websocket):
        assert message.result is not None
        if idx == len(multiple_subscriptions) - 1:
            break
    balance = await test_http_client_async.get_balance(stubbed_sender.public_key, Finalized)
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.integration
async def test_account_subscribe(
    test_http_client_async: AsyncClient, websocket: SolanaWsClientProtocol, account_subscribed: PublicKey
):
    """Test account subscription."""
    await test_http_client_async.request_airdrop(account_subscribed, AIRDROP_AMOUNT)
    main_resp = await websocket.recv()
    assert main_resp.result.value.lamports == AIRDROP_AMOUNT


@pytest.mark.integration
async def test_logs_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClientProtocol,
    logs_subscribed: None,
):
    """Test logs subscription."""
    recipient = Keypair().public_key
    await test_http_client_async.request_airdrop(recipient, AIRDROP_AMOUNT)
    main_resp = await websocket.recv()
    assert main_resp.result.value.logs[0] == "Program 11111111111111111111111111111111 invoke [1]"


@pytest.mark.integration
async def test_logs_subscribe_mentions_filter(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClientProtocol,
    logs_subscribed_mentions_filter: None,
):
    """Test logs subscription with a mentions filter."""
    recipient = Keypair().public_key
    await test_http_client_async.request_airdrop(recipient, AIRDROP_AMOUNT)
    main_resp = await websocket.recv()
    assert main_resp.result.value.logs[0] == "Program 11111111111111111111111111111111 invoke [1]"


@pytest.mark.integration
async def test_program_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClientProtocol,
    program_subscribed: Tuple[PublicKey, PublicKey],
):
    """Test program subscription."""
    program, owned = program_subscribed
    instruction = sp.assign(sp.AssignParams(account_pubkey=owned.public_key, program_id=program.public_key))
    transaction = Transaction()
    transaction.add(instruction)
    await test_http_client_async.send_transaction(transaction, owned)
    main_resp = await websocket.recv()
    assert main_resp.result.value.pubkey == owned.public_key


@pytest.mark.integration
async def test_signature_subscribe(
    websocket: SolanaWsClientProtocol,
    signature_subscribed: None,
):
    """Test signature subscription."""
    main_resp = await websocket.recv()
    assert main_resp.result.value.err is None


@pytest.mark.integration
async def test_slot_subscribe(
    websocket: SolanaWsClientProtocol,
    slot_subscribed: None,
):
    """Test slot subscription."""
    main_resp = await websocket.recv()
    assert main_resp.result.root >= 0


@pytest.mark.integration
async def test_slots_updates_subscribe(
    websocket: SolanaWsClientProtocol,
    slots_updates_subscribed: None,
):
    """Test slots updates subscription."""
    async for idx, resp in asyncstdlib.enumerate(websocket):
        assert resp.result.slot > 0
        if idx == 40:
            break


@pytest.mark.integration
async def test_root_subscribe(
    websocket: SolanaWsClientProtocol,
    root_subscribed: None,
):
    """Test root subscription."""
    main_resp = await websocket.recv()
    assert main_resp.result >= 0


@pytest.mark.integration
async def test_vote_subscribe(
    websocket: SolanaWsClientProtocol,
    vote_subscribed: None,
):
    """Test vote subscription."""
    main_resp = await websocket.recv()
    assert main_resp.result.slots
