"""Tests for the Websocket Client."""
from typing import List, Tuple
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
from solana.rpc.types import TxOpts
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana import system_program as sp
from solana.transaction import Transaction
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


@pytest.fixture
async def logs_subscribed(stubbed_sender: Keypair, websocket: SolanaWsClientProtocol) -> None:
    await websocket.logs_subscribe()
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.logs_unsubscribe(subscription_id)


@pytest.fixture
async def program_subscribed(
    websocket: SolanaWsClientProtocol, test_http_client_async: AsyncClient
) -> Tuple[Keypair, Keypair]:
    program = Keypair()
    owned = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(owned.public_key, AIRDROP_AMOUNT)
    await test_http_client_async.confirm_transaction(airdrop_resp["result"])
    await websocket.program_subscribe(program.public_key)
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield program, owned
    await websocket.program_unsubscribe(subscription_id)


@pytest.fixture
async def signature_subscribed(
    websocket: SolanaWsClientProtocol, test_http_client_async: AsyncClient
) -> Tuple[Keypair, Keypair]:
    recipient = Keypair()
    airdrop_resp = await test_http_client_async.request_airdrop(recipient.public_key, AIRDROP_AMOUNT)
    await websocket.signature_subscribe(airdrop_resp["result"])
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.signature_unsubscribe(subscription_id)


@pytest.fixture
async def signature_subscribed_bad_tx(
    websocket: SolanaWsClientProtocol, test_http_client_async: AsyncClient
) -> Tuple[Keypair, Keypair]:
    program = Keypair()
    owned = Keypair()
    ix = sp.assign(sp.AssignParams(account_pubkey=owned.public_key, program_id=program.public_key))
    tx = Transaction()
    tx.add(ix)
    tx_resp = await test_http_client_async.send_transaction(tx, owned, opts=TxOpts(skip_preflight=True))
    await websocket.signature_subscribe(tx_resp["result"])
    first_resp = await websocket.recv()
    subscription_id = first_resp.result
    yield
    await websocket.signature_unsubscribe(subscription_id)


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
    await test_http_client_async.request_airdrop(account_subscribed, AIRDROP_AMOUNT)
    main_resp = await websocket.recv()
    assert main_resp.result.value.lamports == AIRDROP_AMOUNT


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logs_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClientProtocol,
    logs_subscribed: None,
):
    recipient = Keypair().public_key
    await test_http_client_async.request_airdrop(recipient, AIRDROP_AMOUNT)
    main_resp = await websocket.recv()
    assert main_resp.result.value.logs[0] == "Program 11111111111111111111111111111111 invoke [1]"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_program_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClientProtocol,
    program_subscribed: Tuple[PublicKey, PublicKey],
):
    program, owned = program_subscribed
    ix = sp.assign(sp.AssignParams(account_pubkey=owned.public_key, program_id=program.public_key))
    tx = Transaction()
    tx.add(ix)
    await test_http_client_async.send_transaction(tx, owned)
    main_resp = await websocket.recv()
    assert main_resp.result.value.pubkey == owned.public_key


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signature_subscribe(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClientProtocol,
    signature_subscribed: None,
):
    main_resp = await websocket.recv()
    assert main_resp.result.value.err is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_signature_subscribe_bad_tx(
    test_http_client_async: AsyncClient,
    websocket: SolanaWsClientProtocol,
    signature_subscribed_bad_tx: None,
):
    main_resp = await websocket.recv()
    print(main_resp)
    assert main_resp.result.value.err is None
