"""Tests for the Websocket Client."""
from json import dumps
import pytest
import asyncstdlib
from jsonrpcclient import request_json, Error

from solana.rpc.async_api import AsyncClient
from solana.rpc.request_builder import AccountSubscribe, LogsSubscribe, LogsSubsrcibeFilter
from solana.keypair import Keypair
from solana.rpc.websocket_api import WebsocketClient

from .utils import AIRDROP_AMOUNT


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_subscriptions(stubbed_sender: Keypair, test_http_client_async: AsyncClient):
    """Test subscribing to multiple feeds."""
    uri = "ws://127.0.0.1:8900"
    # async with websockets.connect(uri) as websocket:  # type: ignore
    async with WebsocketClient(uri) as websocket:  # type: ignore
        bad_req = request_json("logsSubscribe", params=["foo"])
        await websocket.send(bad_req)  # None
        bad_req_resp = await websocket.recv()
        assert isinstance(bad_req_resp, Error)
        reqs = [
            LogsSubscribe(filter_=LogsSubsrcibeFilter.ALL).to_request(),
            AccountSubscribe(stubbed_sender.public_key).to_request(),
        ]
        reqs_str = dumps(reqs)
        await websocket.send(reqs_str)  # None
        first_resp = await websocket.recv()
        print(f"first_resp: {first_resp}")
        await test_http_client_async.request_airdrop(stubbed_sender.public_key, AIRDROP_AMOUNT)
        async for idx, message in asyncstdlib.enumerate(websocket):
            print(message)
            if idx == len(reqs) - 1:
                break
        balance = await test_http_client_async.get_balance(
            stubbed_sender.public_key,
        )
        assert balance["result"]["value"] == AIRDROP_AMOUNT


@pytest.mark.asyncio
@pytest.mark.integration
async def test_account_subscribe(stubbed_sender: Keypair, test_http_client_async: AsyncClient):
    """Test air drop to stubbed_sender."""
    uri = "ws://127.0.0.1:8900"
    async with WebsocketClient(uri) as websocket:  # type: ignore
        req = AccountSubscribe(stubbed_sender.public_key).to_request()
        req_str = dumps(req)
        await websocket.send(req_str)  # None
        first_resp = await websocket.recv()
        print(f"first_resp: {first_resp}")
        await test_http_client_async.request_airdrop(stubbed_sender.public_key, AIRDROP_AMOUNT)
        main_resp = await websocket.recv()
        print(f"main_resp: {main_resp}")
