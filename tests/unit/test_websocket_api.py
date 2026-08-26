"""Test websocket API helpers."""

from __future__ import annotations

import itertools

from solders.account_decoder import UiAccountEncoding, UiDataSliceConfig
from solders.commitment_config import CommitmentLevel
from solders.pubkey import Pubkey
from solders.rpc.config import RpcAccountInfoConfig, RpcProgramAccountsConfig
from solders.rpc.filter import Memcmp

from solana.rpc.commitment import Processed
from solana.rpc.models import DataSliceOpts, MemcmpOpts
from solana.rpc.websocket_api import SolanaWsClientProtocol, connect


async def test_account_subscribe_returns_request_id(monkeypatch):
    """Subscription helpers should return the request id used for the request."""
    protocol = SolanaWsClientProtocol.__new__(SolanaWsClientProtocol)
    protocol.request_counter = itertools.count()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    request_id = await protocol.account_subscribe(Pubkey.default())

    assert request_id == 1
    assert sent_messages[0].id == request_id


async def test_slot_subscribe_returns_request_id(monkeypatch):
    """Single-argument subscribe helpers should also return their request id."""
    protocol = SolanaWsClientProtocol.__new__(SolanaWsClientProtocol)
    protocol.request_counter = itertools.count()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    request_id = await protocol.slot_subscribe()

    assert request_id == 1
    assert sent_messages[0].id == request_id


async def test_program_subscribe_with_config(monkeypatch):
    """program_subscribe should accept Pydantic DataSliceOpts/MemcmpOpts models."""
    protocol = SolanaWsClientProtocol.__new__(SolanaWsClientProtocol)
    protocol.request_counter = itertools.count()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    program_id = Pubkey.default()
    request_id = await protocol.program_subscribe(
        program_id,
        commitment=Processed,
        encoding="base64",
        data_slice=DataSliceOpts(offset=1, length=2),
        filters=[17, MemcmpOpts(offset=4, bytes="3Mc6vR")],
    )

    expected_config = RpcProgramAccountsConfig(
        RpcAccountInfoConfig(
            encoding=UiAccountEncoding.Base64,
            commitment=CommitmentLevel.Processed,
            data_slice=UiDataSliceConfig(offset=1, length=2),
        ),
        [17, Memcmp(offset=4, bytes_="3Mc6vR")],
    )
    assert request_id == 1
    assert sent_messages[0].id == request_id
    assert sent_messages[0].config == expected_config


async def test_unsubscribe_sends_server_assigned_subscription_id(monkeypatch):
    """Unsubscribe helpers should translate a subscribe() request ID into the server-assigned subscription ID."""
    protocol = SolanaWsClientProtocol.__new__(SolanaWsClientProtocol)
    protocol.subscriptions = {}
    protocol.sent_subscriptions = {}
    protocol.failed_subscriptions = {}
    protocol.request_ids_to_subscriptions = {}
    protocol.request_counter = itertools.count()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    request_id = await protocol.slot_subscribe()
    protocol.sent_subscriptions[request_id] = sent_messages[0]
    server_subscription = 9710270
    confirmation = f'{{"jsonrpc":"2.0","result":{server_subscription},"id":{request_id}}}'
    protocol._process_rpc_response(confirmation)

    await protocol.slot_unsubscribe(request_id)

    assert f'"params":[{server_subscription}]' in sent_messages[1].to_json()
    assert server_subscription not in protocol.subscriptions
    assert request_id not in protocol.request_ids_to_subscriptions


async def test_unsubscribe_before_confirmation_sends_given_id(monkeypatch):
    """Unsubscribing an unconfirmed subscription should pass the given ID through instead of raising."""
    protocol = SolanaWsClientProtocol.__new__(SolanaWsClientProtocol)
    protocol.subscriptions = {}
    protocol.sent_subscriptions = {}
    protocol.failed_subscriptions = {}
    protocol.request_ids_to_subscriptions = {}
    protocol.request_counter = itertools.count()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    await protocol.logs_unsubscribe(7)

    assert '"params":[7]' in sent_messages[0].to_json()


async def test_connect_preserves_async_with_and_custom_connection(monkeypatch):
    """The connect helper should stay usable as an async context manager."""
    captured = {}
    sentinel_connection = object()

    class FakeConnectionManager:
        async def __aenter__(self):
            return sentinel_connection

        async def __aexit__(self, *args):
            return None

    def fake_ws_connect(uri, **kwargs):
        captured["uri"] = uri
        captured["kwargs"] = kwargs
        return FakeConnectionManager()

    monkeypatch.setattr("solana.rpc.websocket_api.ws_connect", fake_ws_connect)

    async with connect(uri="ws://example") as connection:
        assert connection is sentinel_connection

    assert captured["uri"] == "ws://example"
    assert captured["kwargs"]["create_connection"] is SolanaWsClientProtocol
