"""Tests for the Websocket Client."""
from json import dumps
import pytest
import websockets
import asyncstdlib
from jsonrpcclient import request_json, request, parse_json, Ok, Error

import solana.system_program as sp
from solana.rpc.api import DataSliceOpt
from solana.rpc.async_api import AsyncClient
from solana.rpc.request_builder import AccountSubscribe, LogsSubscribe, LogsSubsrcibeFilter
from solana.keypair import Keypair
from solana.rpc.core import RPCException
from solana.rpc.types import RPCError
from solana.transaction import Transaction
from solana.rpc.commitment import Finalized
from spl.token.constants import WRAPPED_SOL_MINT

from .utils import AIRDROP_AMOUNT, assert_valid_response


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_subscriptions(stubbed_sender: Keypair, test_http_client_async: AsyncClient):
    """Test air drop to stubbed_sender."""
    uri = "ws://127.0.0.1:8900"
    async with websockets.connect(uri) as websocket:  # type: ignore
        bad_req = request_json("logsSubscribe", params=["foo"])
        await websocket.send(bad_req)  # None
        bad_req_resp = await websocket.recv()
        assert isinstance(parse_json(bad_req_resp), Error)
        reqs = [
            LogsSubscribe(filter_=LogsSubsrcibeFilter.ALL).to_request(),
            AccountSubscribe(stubbed_sender.public_key).to_request(),
        ]
        reqs_str = dumps(reqs)
        # req = request_json("logsSubscribe", params=["all"])
        await websocket.send(reqs_str)  # None
        first_resp = await websocket.recv()
        print(f"first_resp: {list(parse_json(first_resp))}")
        await test_http_client_async.request_airdrop(stubbed_sender.public_key, AIRDROP_AMOUNT)
        async for idx, message in asyncstdlib.enumerate(websocket):
            print(message)
            if idx == len(reqs) - 1:
                break
        balance = await test_http_client_async.get_balance(
            stubbed_sender.public_key,
        )
        assert balance["result"]["value"] == AIRDROP_AMOUNT
