"""Test websocket API helpers."""

from __future__ import annotations

import itertools
import logging

import pytest
from solders.account_decoder import UiAccountEncoding, UiDataSliceConfig
from solders.commitment_config import CommitmentLevel
from solders.pubkey import Pubkey
from solders.rpc.config import RpcAccountInfoConfig, RpcProgramAccountsConfig
from solders.rpc.filter import Memcmp
from solders.rpc.requests import LogsUnsubscribe

from solana.rpc.commitment import Processed
from solana.rpc.models import DataSliceOpts, MemcmpOpts
from solana.rpc.websocket_api import SolanaWsClientProtocol, connect


def _ws_protocol() -> SolanaWsClientProtocol:
    protocol = SolanaWsClientProtocol.__new__(SolanaWsClientProtocol)
    protocol.subscriptions = {}
    protocol.sent_subscriptions = {}
    protocol.failed_subscriptions = {}
    protocol.request_ids_to_subscriptions = {}
    protocol.request_counter = itertools.count()
    return protocol


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
    protocol = _ws_protocol()
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


async def test_unsubscribe_before_confirmation_sends_given_id(monkeypatch, caplog):
    """Unsubscribing an unconfirmed subscription should pass the given ID through instead of raising."""
    protocol = _ws_protocol()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    with caplog.at_level(logging.WARNING, logger="solana.rpc.websocket_api"):
        await protocol.logs_unsubscribe(7)

    assert '"params":[7]' in sent_messages[0].to_json()
    assert "7" in caplog.text


async def test_unsubscribe_server_id_wins_when_it_collides_with_request_id(monkeypatch):
    """A server-assigned ID must not be rewritten through the request-ID map."""
    protocol = _ws_protocol()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    slot_req = await protocol.slot_subscribe()
    protocol.sent_subscriptions[slot_req] = sent_messages[-1]
    protocol._process_rpc_response('{"jsonrpc":"2.0","result":1,"id":1}')
    await protocol.slot_unsubscribe(1)

    root_req = await protocol.root_subscribe()
    protocol.sent_subscriptions[root_req] = sent_messages[-1]
    protocol._process_rpc_response('{"jsonrpc":"2.0","result":2,"id":3}')

    vote_req = await protocol.vote_subscribe()
    protocol.sent_subscriptions[vote_req] = sent_messages[-1]
    protocol._process_rpc_response('{"jsonrpc":"2.0","result":3,"id":4}')

    await protocol.vote_unsubscribe(3)

    assert '"method":"voteUnsubscribe"' in sent_messages[-1].to_json()
    assert '"params":[3]' in sent_messages[-1].to_json()
    assert 3 not in protocol.subscriptions
    assert 2 in protocol.subscriptions
    assert protocol.request_ids_to_subscriptions == {3: 2}


async def test_unsubscribe_by_server_id_drops_request_id_mapping(monkeypatch):
    """Unsubscribing with the README server-ID form should still drop the reverse map."""
    protocol = _ws_protocol()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    request_id = await protocol.slot_subscribe()
    protocol.sent_subscriptions[request_id] = sent_messages[0]
    protocol._process_rpc_response('{"jsonrpc":"2.0","result":99,"id":1}')

    await protocol.slot_unsubscribe(99)

    assert '"params":[99]' in sent_messages[-1].to_json()
    assert protocol.subscriptions == {}
    assert protocol.request_ids_to_subscriptions == {}


async def test_unsubscribe_keeps_bookkeeping_if_send_fails(monkeypatch):
    """Local state must stay intact when the unsubscribe request never leaves the client."""
    protocol = _ws_protocol()
    sent_messages = []

    async def fake_send_request(self, message):
        sent_messages.append(message)
        if len(sent_messages) > 1:
            raise ConnectionError("closed")

    monkeypatch.setattr(SolanaWsClientProtocol, "send_request", fake_send_request)

    request_id = await protocol.slot_subscribe()
    protocol.sent_subscriptions[request_id] = sent_messages[0]
    protocol._process_rpc_response('{"jsonrpc":"2.0","result":99,"id":1}')

    with pytest.raises(ConnectionError):
        await protocol.slot_unsubscribe(request_id)

    assert 99 in protocol.subscriptions
    assert protocol.request_ids_to_subscriptions == {1: 99}


async def test_raw_unsubscribe_send_request_forgets_mapping():
    """Raw batched unsubscribes should drop the request-ID map, not only the helper path."""
    protocol = _ws_protocol()
    protocol.subscriptions[9] = object()
    protocol.request_ids_to_subscriptions[1] = 9
    sent = []

    async def fake_send(data):
        sent.append(data)

    protocol.send = fake_send  # type: ignore[method-assign]
    await protocol.send_request(LogsUnsubscribe(9, 2))

    assert sent
    assert 9 not in protocol.subscriptions
    assert protocol.request_ids_to_subscriptions == {}


async def test_signature_notification_forgets_expired_subscription():
    """Signature subscriptions expire server-side after the notification."""
    protocol = _ws_protocol()
    protocol.subscriptions[42] = object()
    protocol.request_ids_to_subscriptions[1] = 42
    protocol._process_rpc_response(
        '{"jsonrpc":"2.0","method":"signatureNotification",'
        '"params":{"result":{"context":{"slot":1},"value":{"err":null}},"subscription":42}}'
    )
    assert 42 not in protocol.subscriptions
    assert protocol.request_ids_to_subscriptions == {}


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
