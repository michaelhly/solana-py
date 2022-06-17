"""This module contains code for interacting with the RPC Websocket endpoint."""
from json import dumps, loads
from typing import Any, Dict, List, Optional, Union, cast

from apischema import deserialize
from jsonrpcclient import Error, Ok, parse
from jsonrpcserver.dispatcher import create_request
from websockets.legacy.client import WebSocketClientProtocol
from websockets.legacy.client import connect as ws_connect

from solana.publickey import PublicKey
from solana.rpc import types
from solana.rpc.commitment import Commitment
from solana.rpc.request_builder import (
    AccountSubscribe,
    AccountUnsubscribe,
    LogsSubscribe,
    LogsSubscribeFilter,
    LogsUnsubscribe,
    MentionsFilter,
    ProgramSubscribe,
    ProgramUnsubscribe,
    RequestBody,
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
from solana.rpc.responses import (
    AccountNotification,
    LogsNotification,
    ProgramNotification,
    RootNotification,
    SignatureNotification,
    SlotNotification,
    SlotsUpdatesNotification,
    SubscriptionNotification,
    VoteNotification,
)
from solana.transaction import TransactionSignature

_NOTIFICATION_MAP = {
    "accountNotification": AccountNotification,
    "logsNotification": LogsNotification,
    "programNotification": ProgramNotification,
    "signatureNotification": SignatureNotification,
    "slotNotification": SlotNotification,
    "rootNotification": RootNotification,
    "slotsUpdatesNotification": SlotsUpdatesNotification,
    "voteNotification": VoteNotification,
}


class SubscriptionError(Exception):
    """Raise when subscribing to an RPC feed fails."""

    def __init__(self, err: Error, subscription: dict) -> None:
        """Init.

        Args:
            err: The RPC error object.
            subscription: The subscription message that caused the error.

        """
        self.code = err.code
        self.msg = err.message
        self.subscription = subscription
        super().__init__(f"{self.code}: {self.msg}\n Caused by subscription: {subscription}")


class SolanaWsClientProtocol(WebSocketClientProtocol):
    """Subclass of `websockets.WebSocketClientProtocol` tailored for Solana RPC websockets."""

    def __init__(self, *args, **kwargs):
        """Init. Args and kwargs are passed to `websockets.WebSocketClientProtocol`."""
        super().__init__(*args, **kwargs)
        self.subscriptions = {}
        self.sent_subscriptions = {}
        self.failed_subscriptions = {}

    async def _send(self, data: Union[Dict[str, Any], list]) -> None:
        as_json_str = dumps(data)
        await super().send(as_json_str)
        if isinstance(data, dict):
            self.sent_subscriptions[data["id"]] = data
        else:
            for req in data:
                self.sent_subscriptions[req["id"]] = req

    async def send_data(self, message: Union[RequestBody, List[RequestBody]]) -> None:
        """Send a subscribe/unsubscribe request or list of requests.

        Basically `.send` from `websockets` with extra parsing.

        Args:
            message: The request(s) to send.
        """
        to_send = message.to_request() if isinstance(message, RequestBody) else [msg.to_request() for msg in message]
        await self._send(to_send)  # type: ignore

    async def recv(  # type: ignore
        self,
    ) -> Union[List[Union[SubscriptionNotification, Error, Ok]], SubscriptionNotification, Error, Ok]:
        """Receive the next message.

        Basically `.recv` from `websockets` with extra parsing.
        """
        data = await super().recv()
        as_json = loads(data)
        if isinstance(as_json, list):
            return [self._process_rpc_response(item) for item in as_json]
        return self._process_rpc_response(as_json)

    async def account_subscribe(
        self, pubkey: PublicKey, commitment: Optional[Commitment] = None, encoding: Optional[str] = None
    ) -> None:
        """Subscribe to an account to receive notifications when the lamports or data change.

        Args:
            pubkey: Account pubkey.
            commitment: Commitment level.
            encoding: Encoding to use.
        """
        req = AccountSubscribe(pubkey, commitment, encoding)
        await self.send_data(req)

    async def account_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from account notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = AccountUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def logs_subscribe(
        self,
        filter_: Union[str, MentionsFilter] = LogsSubscribeFilter.ALL,
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
    ) -> None:
        """Subscribe to transaction logging.

        Args:
            filter_: filter criteria for the logs. Use `LogsSubscribeFilter` to build the filter.
            commitment: The commitment level to use.
            encoding: The encoding to use.
        """
        req = LogsSubscribe(filter_, commitment, encoding)
        await self.send_data(req)

    async def logs_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from transaction logging.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = LogsUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def program_subscribe(  # pylint: disable=too-many-arguments
        self,
        program_id: PublicKey,
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
        data_size: Optional[int] = None,
        memcmp_opts: Optional[List[types.MemcmpOpts]] = None,
    ) -> None:
        """Receive notifications when the lamports or data for a given account owned by the program changes.

        Args:
            program_id: The program ID.
            commitment: Commitment level to use.
            encoding: Encoding to use.
            data_size: Data size filter.
            memcmp_opts: memcmp options.
        """  # noqa: E501
        req = ProgramSubscribe(program_id, commitment, encoding, data_size, memcmp_opts)
        await self.send_data(req)

    async def program_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from program account notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = ProgramUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def signature_subscribe(
        self,
        signature: TransactionSignature,
        commitment: Optional[Commitment] = None,
    ) -> None:
        """Subscribe to a transaction signature to receive notification when the transaction is confirmed.

        Args:
            signature: The transaction signature to subscribe to.
            commitment: Commitment level.
        """
        req = SignatureSubscribe(signature, commitment)
        await self.send_data(req)

    async def signature_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from signature notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = SignatureUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def slot_subscribe(self) -> None:
        """Subscribe to receive notification anytime a slot is processed by the validator."""
        req = SlotSubscribe()
        await self.send_data(req)

    async def slot_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from slot notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = SlotUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def slots_updates_subscribe(self) -> None:
        """Subscribe to receive a notification from the validator on a variety of updates on every slot."""
        req = SlotsUpdatesSubscribe()
        await self.send_data(req)

    async def slots_updates_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from slot update notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = SlotsUpdatesUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def root_subscribe(self) -> None:
        """Subscribe to receive notification anytime a new root is set by the validator."""
        req = RootSubscribe()
        await self.send_data(req)

    async def root_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from root notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = RootUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def vote_subscribe(self) -> None:
        """Subscribe to receive notification anytime a new vote is observed in gossip."""
        req = VoteSubscribe()
        await self.send_data(req)

    async def vote_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from vote notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req = VoteUnsubscribe(subscription)
        await self.send_data(req)
        del self.subscriptions[subscription]

    def _process_rpc_response(self, data: dict) -> Union[SubscriptionNotification, Error, Ok]:
        parsed = _parse_rpc_response(data)
        if isinstance(parsed, Error):
            subscription = self.sent_subscriptions[parsed.id]
            self.failed_subscriptions[parsed.id] = subscription
            raise SubscriptionError(parsed, subscription)
        parsed_result = parsed.result
        if type(parsed_result) is int and type(parsed) is Ok:  # pylint: disable=unidiomatic-typecheck
            self.subscriptions[parsed_result] = self.sent_subscriptions[parsed.id]
        return parsed


def _parse_rpc_response(data: dict) -> Union[SubscriptionNotification, Error, Ok]:
    if "params" in data:
        req = create_request(data)
        dtype = _NOTIFICATION_MAP[req.method]
        res: SubscriptionNotification = deserialize(dtype, req.params)
        return res
    return cast(Union[Ok, Error], parse(data))


class connect(ws_connect):  # pylint: disable=invalid-name,too-few-public-methods
    """Solana RPC websocket connector."""

    def __init__(self, uri: str = "ws://localhost:8900", **kwargs: Any) -> None:
        """Init. Kwargs are passed to `websockets.connect`.

        Args:
            uri: The websocket endpoint.
        """
        super().__init__(uri, **kwargs, create_protocol=SolanaWsClientProtocol)
