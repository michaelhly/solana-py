"""Confirmed Solana WebSocket subscriptions and JSON-RPC request dispatch."""

from __future__ import annotations

import asyncio
import itertools
import json
import math
from collections import deque
from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass
from enum import Enum, StrEnum
from types import TracebackType
from typing import Any, Generic, TypeVar, cast

from solders.rpc.config import (
    RpcAccountInfoConfig,
    RpcBlockSubscribeFilter,
    RpcBlockSubscribeConfig,
    RpcProgramAccountsConfig,
    RpcSignatureSubscribeConfig,
    RpcTransactionLogsConfig,
    RpcTransactionLogsFilter,
    RpcTransactionLogsFilterMentions,
)
from solders.account_decoder import UiDataSliceConfig
from solders.rpc.filter import Memcmp
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction_status import TransactionDetails
from solders.rpc.requests import (
    AccountSubscribe,
    AccountUnsubscribe,
    BlockSubscribe,
    BlockUnsubscribe,
    LogsSubscribe,
    LogsUnsubscribe,
    ProgramSubscribe,
    ProgramUnsubscribe,
    RootSubscribe,
    RootUnsubscribe,
    SignatureSubscribe,
    SignatureUnsubscribe,
    SlotSubscribe,
    SlotsUpdatesSubscribe,
    SlotsUpdatesUnsubscribe,
    SlotUnsubscribe,
    VoteSubscribe,
    VoteUnsubscribe,
)
from solders.rpc.responses import (
    Notification,
    SignatureNotification,
    SubscriptionResult,
    UnsubscribeResult,
    parse_websocket_message,
    WebsocketMessage,
)
from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import (
    ConcurrencyError,
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
    ProtocolError,
)
from websockets.frames import Close, CloseCode

from solana.rpc.jsonrpc import (
    JsonRpcErrorObject,
    JsonRpcRequestSerializer,
    JsonRpcResponseEnvelope,
    SolanaJsonRpcError,
)
from solana.rpc.core import (
    _ACCOUNT_ENCODING_TO_SOLDERS,
    _COMMITMENT_TO_SOLDERS,
    _TX_ENCODING_TO_SOLDERS,
)
from solana.rpc.models import DataSliceOpts, MemcmpOpts
from solana.rpc.commitment import Commitment

T = TypeVar("T")


class SubscriptionKind(StrEnum):
    """Solana subscription methods supported by the typed helpers."""

    ACCOUNT = "account"
    BLOCK = "block"
    LOGS = "logs"
    PROGRAM = "program"
    SIGNATURE = "signature"
    SLOT = "slot"
    SLOTS_UPDATES = "slotsUpdates"
    ROOT = "root"
    VOTE = "vote"


_UNSUBSCRIBE_REQUESTS: dict[SubscriptionKind, Callable[[int, int], JsonRpcRequestSerializer]] = {
    SubscriptionKind.ACCOUNT: AccountUnsubscribe,
    SubscriptionKind.BLOCK: BlockUnsubscribe,
    SubscriptionKind.LOGS: LogsUnsubscribe,
    SubscriptionKind.PROGRAM: ProgramUnsubscribe,
    SubscriptionKind.SIGNATURE: SignatureUnsubscribe,
    SubscriptionKind.SLOT: SlotUnsubscribe,
    SubscriptionKind.SLOTS_UPDATES: SlotsUpdatesUnsubscribe,
    SubscriptionKind.ROOT: RootUnsubscribe,
    SubscriptionKind.VOTE: VoteUnsubscribe,
}


@dataclass(frozen=True, slots=True)
class Subscription:
    """A server-confirmed subscription owned by one physical connection.

    Handles are created by subscribe helpers. Copying or reconstructing a handle
    doesn't grant ownership; unsubscribe checks its object identity.
    """

    subscription_id: int
    kind: SubscriptionKind


class ConnectionState(Enum):
    """Lifecycle of the RPC dispatcher, independent of the wire protocol state."""

    OPEN = "open"
    CLOSED = "closed"


class OverflowPolicy(StrEnum):
    """What a full notification queue does to the next notification.

    Blocking the reader is deliberately not offered: it also stops RPC
    responses, so ``unsubscribe`` -- the one call that could drain the flood --
    would never be confirmed, and the unread socket stalls the closing
    handshake. Both lossy policies count what they discard in
    :attr:`SolanaWsClient.dropped_notifications`.
    """

    RAISE = "raise"
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"


class UnsubscribeError(Exception):
    """The server explicitly refused to cancel a subscription."""

    def __init__(self, subscription: Subscription) -> None:
        """Retain the handle whose unsubscribe request returned false."""
        self.subscription = subscription
        super().__init__(f"Unsubscribe returned false for {subscription.kind.value} {subscription.subscription_id}")


@dataclass(slots=True)
class _PendingRequest(Generic[T]):
    request_id: int
    future: asyncio.Future[T]
    method: str
    # Set for subscribe requests, whose result must become a registered handle.
    kind: SubscriptionKind | None = None
    send_started: bool = False


def _positive_timeout(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return float(value)


def _parse_frame(text: str) -> list[JsonRpcResponseEnvelope | WebsocketMessage]:
    """Parse one frame, keeping error envelopes away from solders.

    solders resolves the numeric code into a typed error and keeps only the
    message, and it panics outright on errors that omit ``data`` -- a panic is
    not an ``Exception``, so the reader could not even record it.
    """
    payload = json.loads(text)
    parsed: list[JsonRpcResponseEnvelope | WebsocketMessage] = []
    for item in payload if isinstance(payload, list) else [payload]:
        if isinstance(item, dict) and "error" in item:
            # JSON-RPC 2.0 section 5 requires a null id when the server could not read
            # the request, so no pending entry can own this error: raising lets the
            # reader abandon the connection with the server's own code and message.
            if item.get("id") is None:
                raise SolanaJsonRpcError.from_error_object(
                    JsonRpcErrorObject.model_validate(item["error"]), request_id=None
                )
            parsed.append(JsonRpcResponseEnvelope.model_validate(item))
        else:
            parsed.extend(parse_websocket_message(json.dumps(item)))
    return parsed


def _consume_future_exception(future: asyncio.Future[Any]) -> None:
    # A cancelled caller may never await the exception set during shutdown.
    if not future.cancelled():
        future.exception()


# RFC 6455 codes that ``websockets`` treats as a clean closure.
_OK_CLOSE_CODES = frozenset({CloseCode.NORMAL_CLOSURE, CloseCode.GOING_AWAY, CloseCode.NO_STATUS_RCVD})


def _local_close_exc(frame: Close) -> ConnectionClosed:
    """Build the exception receivers see for a close this client initiated.

    Decided here, when the close is requested, rather than read back from the
    protocol later: ``protocol.close_exc`` is only valid once the closing
    handshake has completed, which is one round trip after waiters are woken.
    """
    exc_type = ConnectionClosedOK if frame.code in _OK_CLOSE_CODES else ConnectionClosedError
    return exc_type(frame, frame, False)


class SolanaWsClient:
    """One reader dispatches RPC responses and delivers typed notifications.

    Use :meth:`connect` to open and manage the connection. Subscribe helpers
    await confirmation and return :class:`Subscription`; :meth:`recv` returns
    notifications only. Fatal errors abort every subscription on this connection.
    """

    def __init__(
        self,
        uri: str = "ws://localhost:8900",
        *,
        request_timeout: float = 10.0,
        notification_queue_size: int = 10_000,
        overflow: OverflowPolicy = OverflowPolicy.RAISE,
        **kwargs: Any,
    ) -> None:
        """Create a client; the WebSocket is opened by :meth:`connect`."""
        self._uri = uri
        self._connect_kwargs = dict(kwargs)
        self._connect_kwargs["close_timeout"] = _positive_timeout(kwargs.get("close_timeout", 10.0), "close_timeout")
        self._ws: ClientConnection | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self.request_timeout = _positive_timeout(request_timeout, "request_timeout")
        if type(notification_queue_size) is not int or notification_queue_size <= 0:
            raise ValueError("notification_queue_size must be a positive integer")
        self._notification_queue_size = notification_queue_size
        self._overflow = OverflowPolicy(overflow)
        self._dropped_notifications = 0
        self._notifications: deque[Notification] = deque()
        self._notification_ready = asyncio.Event()
        self._receiving = False
        self._connect_lock = asyncio.Lock()
        self._pending_requests: dict[int, _PendingRequest[Any]] = {}
        self._request_counter = itertools.count(1)
        self._subscriptions: dict[int, Subscription] = {}
        self._unsubscribing: set[int] = set()
        self._send_lock = asyncio.Lock()
        self._closed_exc: BaseException | None = None
        self._reader_task: asyncio.Task[None] | None = None

    async def connect(self) -> SolanaWsClient:
        """Open and own the native WebSocket, then start its sole reader."""
        async with self._connect_lock:
            if self.connection_state is ConnectionState.OPEN:
                return self
            # A failed handshake owns nothing, so only a used client is refused.
            if self._ws is not None or self._closed_exc is not None:
                raise RuntimeError("SolanaWsClient instances cannot be reused")
            # Pinned before the first loop-bound resource exists, so every task and future shares one loop.
            loop = self._loop = asyncio.get_running_loop()
            self._ws = await ws_connect(self._uri, **self._connect_kwargs)
            self._reader_task = loop.create_task(self._read_loop(), name="solana-ws-reader")
            return self

    async def __aenter__(self) -> SolanaWsClient:
        """Connect this client for use as an async context manager."""
        return await self.connect()

    @property
    def connection_state(self) -> ConnectionState:
        """Return the RPC dispatcher's lifecycle state."""
        if self._ws is None or self._closed_exc is not None:
            return ConnectionState.CLOSED
        return ConnectionState.OPEN

    @property
    def dropped_notifications(self) -> int:
        """Count notifications a lossy overflow policy discarded; always 0 under ``RAISE``."""
        return self._dropped_notifications

    def _abandon(self, exc: BaseException) -> None:
        """Record why the stream ended and wake every waiter; the first cause wins.

        A reader task cannot raise into the caller's stack, so the cause is
        stored here and re-raised by whoever is waiting.
        """
        if self._closed_exc is not None:
            return
        self._closed_exc = exc
        self._notification_ready.set()
        for pending in self._pending_requests.values():
            if not pending.future.done():
                pending.future.set_exception(exc)
        # Subscriptions are owned by one physical connection and die with it.
        self._subscriptions.clear()

    async def close(self, code: int = CloseCode.NORMAL_CLOSURE, reason: str = "") -> None:
        """Release the connection; the only cleanup path, idempotent and safe to call concurrently."""
        frame = Close(code, reason)
        frame.check()
        self._abandon(_local_close_exc(frame))
        loop = self._loop
        if self._ws is None or loop is None:
            return
        # Shielded so a cancelled caller -- a repeated Ctrl+C -- cannot abandon a half-closed socket.
        release = loop.create_task(self._release(frame), name="solana-ws-release")
        try:
            await asyncio.shield(release)
        except asyncio.CancelledError:
            await asyncio.shield(release)
            raise

    async def _release(self, frame: Close) -> None:
        ws = self._ws
        try:
            if ws is not None:
                # Idempotent, bounded by close_timeout, and aborts the transport if that elapses.
                await ws.close(frame.code, frame.reason)
        finally:
            reader = self._reader_task
            if reader is not None:
                reader.cancel()
                await asyncio.gather(reader, return_exceptions=True)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Report the context's own failure to waiters, then always release the socket."""
        if exc_value is not None:
            self._abandon(exc_value)
        await self.close()

    async def recv(self) -> Notification:
        """Receive one notification; cancellation leaves queued notifications intact.

        Only one caller may receive at a time. Notifications already received
        are delivered before the closure is reported, as ``websockets``' own
        ``recv()`` does. Raw text/bytes decoding isn't supported.
        """
        if self._receiving:
            raise ConcurrencyError("Only one notification receiver may run at a time")
        self._receiving = True
        try:
            while True:
                if self._notifications:
                    return self._notifications.popleft()
                if self._closed_exc is not None:
                    raise self._closed_exc
                if self._ws is None:
                    raise RuntimeError("WebSocket is not connected")
                self._notification_ready.clear()
                await self._notification_ready.wait()
        finally:
            self._receiving = False

    async def __aiter__(self) -> AsyncIterator[Notification]:
        """Iterate over notifications until a normal connection closure."""
        try:
            while True:
                yield await self.recv()
        except ConnectionClosedOK:
            return

    async def _read_loop(self) -> None:
        ws = self._ws
        if ws is None:
            return
        try:
            while self._closed_exc is None:
                raw = await ws.recv()
                for envelope in _parse_frame(raw.decode() if isinstance(raw, bytes) else raw):
                    if self._closed_exc is not None:
                        return
                    if isinstance(envelope, JsonRpcResponseEnvelope):
                        self._dispatch_error(envelope)
                    elif isinstance(envelope, (SubscriptionResult, UnsubscribeResult)):
                        self._dispatch_response(envelope)
                    else:
                        self._dispatch_notification(cast(Notification, envelope))
        # The reader records every failure of this connection.
        except Exception as exc:  # noqa: BLE001
            self._abandon(exc)

    def _dispatch_error(self, envelope: JsonRpcResponseEnvelope) -> None:
        pending = self._pending_requests.pop(cast(int, envelope.id), None)
        if pending is None:
            return
        pending.future.set_exception(
            SolanaJsonRpcError.from_error_object(
                cast(JsonRpcErrorObject, envelope.error),
                request_id=envelope.id,
                method=pending.method,
            )
        )

    def _dispatch_response(self, envelope: SubscriptionResult | UnsubscribeResult) -> None:
        request_id = envelope.id
        # Popping first makes dispatch idempotent: a response for a request that
        # already timed out, was cancelled, or arrives twice has no waiter left.
        pending = self._pending_requests.pop(request_id, None)
        if pending is None:
            return
        if pending.kind is not None:
            # Registered before the caller is woken: the reader keeps draining
            # frames while that coroutine is merely scheduled, so a notification
            # following the confirmation must already find the handle.
            pending.future.set_result(self._register_subscription(pending.kind, cast(int, envelope.result)))
        else:
            # No kind means an unsubscribe, whose result is the server's boolean.
            pending.future.set_result(envelope.result)

    def _dispatch_notification(self, notification: Notification) -> None:
        subscription_id = notification.subscription
        if isinstance(notification, SignatureNotification):
            self._subscriptions.pop(subscription_id, None)
        if len(self._notifications) >= self._notification_queue_size:
            if self._overflow is OverflowPolicy.RAISE:
                raise ProtocolError("WebSocket notification queue overflow")
            self._dropped_notifications += 1
            if self._overflow is OverflowPolicy.DROP_NEWEST:
                return
            self._notifications.popleft()
        self._notifications.append(notification)
        self._notification_ready.set()

    async def _request(
        self,
        request: JsonRpcRequestSerializer,
        kind: SubscriptionKind | None = None,
    ) -> _PendingRequest[T]:
        ws, loop = self._ws, self._loop
        if self.connection_state is not ConnectionState.OPEN or ws is None or loop is None:
            raise RuntimeError("WebSocket is not connected")
        serialized = request.to_json()
        body = json.loads(serialized)
        # solders request serializers produce valid JSON-RPC envelopes.
        # The protocol serializer exposes ``id`` at runtime; the shared
        # serializer type omits that concrete request attribute.
        request_id = cast(Any, request).id
        future: asyncio.Future[T] = cast(asyncio.Future[T], loop.create_future())
        future.add_done_callback(_consume_future_exception)
        pending = _PendingRequest(request_id, future, body["method"], kind)
        self._pending_requests[request_id] = pending
        try:
            async with self._send_lock:
                if self._closed_exc is not None:
                    raise self._closed_exc
                pending.send_started = True
                try:
                    await ws.send(serialized)
                except Exception as exc:
                    self._abandon(exc)
                    raise
        except BaseException:
            self._pending_requests.pop(request_id, None)
            if not future.done():
                future.cancel()
            raise
        return pending

    async def _wait_pending(self, pending: _PendingRequest[T], timeout: float | None = None) -> T:
        """Await a registered request and remove it on caller cancellation/timeout."""
        duration = self.request_timeout if timeout is None else _positive_timeout(timeout, "timeout")
        timer = asyncio.timeout(duration)
        try:
            async with timer:
                return await asyncio.shield(pending.future)
        except asyncio.CancelledError as exc:
            if pending.send_started:
                self._abandon(exc)
            raise
        except TimeoutError as exc:
            if pending.send_started and timer.expired():
                self._abandon(exc)
            raise
        finally:
            self._pending_requests.pop(pending.request_id, None)
            if not pending.future.done():
                pending.future.cancel()

    async def _subscribe(
        self,
        kind: SubscriptionKind,
        request: JsonRpcRequestSerializer,
    ) -> Subscription:
        pending: _PendingRequest[Subscription] = await self._request(request, kind)
        return await self._wait_pending(pending)

    def _register_subscription(self, kind: SubscriptionKind, subscription_id: int) -> Subscription:
        subscription = Subscription(subscription_id, kind)
        self._subscriptions[subscription_id] = subscription
        return subscription

    def _remove_subscription(self, subscription_id: int) -> None:
        self._subscriptions.pop(subscription_id, None)

    def _unsubscribe_request(self, subscription: Subscription) -> JsonRpcRequestSerializer:
        """Build the JSON-RPC request that cancels a subscription."""
        request_type = _UNSUBSCRIBE_REQUESTS[subscription.kind]
        return request_type(subscription.subscription_id, next(self._request_counter))

    async def unsubscribe(self, subscription: Subscription) -> None:
        """Cancel a live subscription after receiving server confirmation.

        Closing the connection already cancels everything it owned, so this is a
        no-op afterwards and never masks the error that ended the stream.
        """
        if self._closed_exc is not None:
            return
        subscription_id = subscription.subscription_id
        if self._subscriptions.get(subscription_id) is not subscription:
            raise ValueError("Subscription handle is no longer active")
        if subscription_id in self._unsubscribing:
            raise ValueError("Unsubscribe is already pending for this handle")
        request = self._unsubscribe_request(subscription)
        self._unsubscribing.add(subscription_id)
        try:
            pending: _PendingRequest[bool] = await self._request(request)
            result = await self._wait_pending(pending)
            if not result:
                raise UnsubscribeError(subscription)
            self._remove_subscription(subscription_id)
        finally:
            self._unsubscribing.discard(subscription_id)

    async def account_subscribe(
        self,
        *,
        pubkey: Pubkey,
        commitment: Commitment | None = None,
        encoding: str | None = None,
        data_slice: DataSliceOpts | None = None,
        min_context_slot: int | None = None,
    ) -> Subscription:
        """Subscribe to account notifications for a public key."""
        config = None
        if any(value is not None for value in (commitment, encoding, data_slice, min_context_slot)):
            account_encoding = _ACCOUNT_ENCODING_TO_SOLDERS[encoding] if encoding is not None else None
            account_commitment = _COMMITMENT_TO_SOLDERS[commitment] if commitment is not None else None
            account_data_slice = (
                UiDataSliceConfig(offset=data_slice.offset, length=data_slice.length) if data_slice else None
            )
            config = RpcAccountInfoConfig(
                account_encoding,
                account_data_slice,
                account_commitment,
                min_context_slot,
            )
        return await self._subscribe(
            SubscriptionKind.ACCOUNT,
            AccountSubscribe(pubkey, config, next(self._request_counter)),
        )

    async def program_subscribe(
        self,
        *,
        program_id: Pubkey,
        commitment: Commitment | None = None,
        encoding: str | None = None,
        data_slice: DataSliceOpts | None = None,
        min_context_slot: int | None = None,
        filters: Sequence[int | MemcmpOpts] | None = None,
        with_context: bool | None = None,
        sort_results: bool | None = None,
    ) -> Subscription:
        """Subscribe to program account notifications."""
        config = None
        if any(
            value is not None
            for value in (
                commitment,
                encoding,
                data_slice,
                min_context_slot,
                filters,
                with_context,
                sort_results,
            )
        ):
            account = RpcAccountInfoConfig(
                encoding=(None if encoding is None else _ACCOUNT_ENCODING_TO_SOLDERS[encoding]),
                commitment=(None if commitment is None else _COMMITMENT_TO_SOLDERS[commitment]),
                min_context_slot=min_context_slot,
                data_slice=(
                    None
                    if data_slice is None
                    else UiDataSliceConfig(offset=data_slice.offset, length=data_slice.length)
                ),
            )
            parsed_filters = (
                None
                if filters is None
                else [x if isinstance(x, int) else Memcmp(offset=x.offset, bytes_=x.bytes) for x in filters]
            )
            config = cast(Any, RpcProgramAccountsConfig)(account, parsed_filters, with_context, sort_results)
        return await self._subscribe(
            SubscriptionKind.PROGRAM,
            ProgramSubscribe(program_id, config, next(self._request_counter)),
        )

    async def logs_subscribe(
        self,
        *,
        filter_: (RpcTransactionLogsFilter | RpcTransactionLogsFilterMentions) = RpcTransactionLogsFilter.All,
        commitment: Commitment | None = None,
    ) -> Subscription:
        """Subscribe to transaction log notifications."""
        logs_commitment = _COMMITMENT_TO_SOLDERS[commitment] if commitment is not None else None
        config = RpcTransactionLogsConfig(logs_commitment)
        return await self._subscribe(
            SubscriptionKind.LOGS,
            LogsSubscribe(filter_, config, next(self._request_counter)),
        )

    async def block_subscribe(
        self,
        *,
        filter_: RpcBlockSubscribeFilter = RpcBlockSubscribeFilter.All,
        commitment: Commitment | None = None,
        encoding: str | None = None,
        transaction_details: TransactionDetails | None = None,
        show_rewards: bool | None = None,
        max_supported_transaction_version: int | None = None,
    ) -> Subscription:
        """Subscribe to block notifications."""
        block_commitment = _COMMITMENT_TO_SOLDERS[commitment] if commitment is not None else None
        block_encoding = _TX_ENCODING_TO_SOLDERS[encoding] if encoding is not None else None
        config = RpcBlockSubscribeConfig(
            block_commitment,
            block_encoding,
            transaction_details,
            show_rewards,
            max_supported_transaction_version,
        )
        return await self._subscribe(
            SubscriptionKind.BLOCK,
            BlockSubscribe(filter_, config, next(self._request_counter)),
        )

    async def signature_subscribe(
        self,
        *,
        signature: Signature,
        commitment: Commitment | None = None,
        enable_received_notification: bool | None = None,
    ) -> Subscription:
        """Subscribe to signature status notifications."""
        config = None
        if commitment is not None or enable_received_notification is not None:
            signature_commitment = _COMMITMENT_TO_SOLDERS[commitment] if commitment is not None else None
            config = RpcSignatureSubscribeConfig(signature_commitment, enable_received_notification)
        return await self._subscribe(
            SubscriptionKind.SIGNATURE,
            SignatureSubscribe(signature, config, next(self._request_counter)),
        )

    async def slot_subscribe(self) -> Subscription:
        """Subscribe to slot notifications."""
        return await self._subscribe(SubscriptionKind.SLOT, SlotSubscribe(next(self._request_counter)))

    async def slots_updates_subscribe(self) -> Subscription:
        """Subscribe to slot update notifications."""
        return await self._subscribe(
            SubscriptionKind.SLOTS_UPDATES,
            SlotsUpdatesSubscribe(next(self._request_counter)),
        )

    async def root_subscribe(self) -> Subscription:
        """Subscribe to root notifications."""
        return await self._subscribe(SubscriptionKind.ROOT, RootSubscribe(next(self._request_counter)))

    async def vote_subscribe(self) -> Subscription:
        """Subscribe to vote notifications."""
        return await self._subscribe(SubscriptionKind.VOTE, VoteSubscribe(next(self._request_counter)))
