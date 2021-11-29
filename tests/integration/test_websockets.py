"""Tests for the Websocket Client."""
from typing import List
import pytest
import asyncstdlib
from jsonrpcclient import request

from solana.rpc.async_api import AsyncClient
from solana.rpc.request_builder import (
    AccountSubscribe,
    AccountUnsubscribe,
    LogsSubscribe,
    LogsSubsrcibeFilter,
    LogsUnsubscribe,
    RequestBody,
)
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.websocket_api import WebsocketClient, SubscriptionError, SolanaWsClientProtocol

from .utils import AIRDROP_AMOUNT


@pytest.fixture
async def websocket(test_http_client_async: AsyncClient) -> SolanaWsClientProtocol:
    """Websocket connection."""
    async with WebsocketClient() as client:
        yield client


@pytest.fixture
async def multiple_subscriptions(stubbed_sender: Keypair, websocket: SolanaWsClientProtocol) -> List[RequestBody]:
    reqs = [
        LogsSubscribe(filter_=LogsSubsrcibeFilter.ALL),
        AccountSubscribe(stubbed_sender.public_key),
    ]
    await websocket.send(reqs)  # None
    first_resp = await websocket.recv()
    logs_subscription_id, account_subscription_id = [resp.result for resp in first_resp]
    yield reqs
    unsubscribe_reqs = [LogsUnsubscribe(logs_subscription_id), AccountUnsubscribe(account_subscription_id)]
    await websocket.send(unsubscribe_reqs)


@pytest.fixture
async def account_subscribed(stubbed_sender: Keypair, websocket: SolanaWsClientProtocol) -> PublicKey:
    recipient = Keypair()
    await websocket.account_subscribe(recipient.public_key)
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield recipient.public_key
    await websocket.account_unsubscribe(subscription_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_subscriptions(
    stubbed_sender: Keypair,
    test_http_client_async: AsyncClient,
    multiple_subscriptions: List[RequestBody],
    websocket: SolanaWsClientProtocol,
):
    """Test subscribing to multiple feeds."""
    await test_http_client_async.request_airdrop(stubbed_sender.public_key, AIRDROP_AMOUNT)
    async for idx, message in asyncstdlib.enumerate(websocket):
        if idx == len(multiple_subscriptions) - 1:
            break
    balance = await test_http_client_async.get_balance(
        stubbed_sender.public_key,
    )
    assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bad_request(websocket: SolanaWsClientProtocol):
    """Test sending a malformed subscription request."""
    bad_req = request("logsSubscribe", params=["foo"])
    await websocket._send(bad_req)  # None
    with pytest.raises(SubscriptionError) as exc_info:
        _ = await websocket.recv()
    assert exc_info.value.code == -32602
    assert exc_info.value.subscription == bad_req


@pytest.mark.asyncio
@pytest.mark.integration
async def test_account_subscribe(
    test_http_client_async: AsyncClient, websocket: SolanaWsClientProtocol, account_subscribed: PublicKey
):
    """Test air drop to stubbed_sender."""
    await test_http_client_async.request_airdrop(account_subscribed, AIRDROP_AMOUNT)
    main_resp = await websocket.recv()
    assert main_resp.result.value.lamports == AIRDROP_AMOUNT
