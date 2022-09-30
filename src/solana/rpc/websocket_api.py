"""This module contains code for interacting with the RPC Websocket endpoint."""
from json import loads
from typing import Any, List, Optional, Union, cast, Sequence
import itertools

from apischema import deserialize
from jsonrpcclient import Error, Ok, parse
from jsonrpcserver.dispatcher import create_request
from websockets.legacy.client import WebSocketClientProtocol
from websockets.legacy.client import connect as ws_connect
from solders.rpc.requests import (
    AccountSubscribe,
    AccountUnsubscribe,
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
    Body,
    batch_to_json,
)
from solders.rpc.config import (
    RpcAccountInfoConfig,
    RpcTransactionLogsFilter,
    RpcTransactionLogsFilterMentions,
    RpcTransactionLogsConfig,
    RpcSignatureSubscribeConfig,
    RpcProgramAccountsConfig,
)
from solders.rpc.filter import Memcmp
from solders.signature import Signature
from solders.account_decoder import UiDataSliceConfig

from solana.publickey import PublicKey
from solana.rpc import types
from solana.rpc.core import _COMMITMENT_TO_SOLDERS, _ACCOUNT_ENCODING_TO_SOLDERS
from solana.rpc.commitment import Commitment
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
        self.request_counter = itertools.count()

    def increment_counter_and_get_id(self) -> int:
        """Increment self.request_counter and return the latest id."""
        return next(self.request_counter) + 1

    async def send_data(self, message: Union[Body, List[Body]]) -> None:
        """Send a subscribe/unsubscribe request or list of requests.

        Basically `.send` from `websockets` with extra parsing.

        Args:
            message: The request(s) to send.
        """
        if isinstance(message, list):
            to_send = batch_to_json(message)
            for req in message:
                self.sent_subscriptions[req.id] = req
        else:
            to_send = message.to_json()
            self.sent_subscriptions[message.id] = message
        await super().send(to_send)  # type: ignore

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
        req_id = self.increment_counter_and_get_id()
        commitment_to_use = None if commitment is None else _COMMITMENT_TO_SOLDERS[commitment]
        encoding_to_use = None if encoding is None else _ACCOUNT_ENCODING_TO_SOLDERS[encoding]
        config = (
            None
            if commitment_to_use is None and encoding_to_use is None
            else RpcAccountInfoConfig(encoding=encoding_to_use, commitment=commitment_to_use)
        )
        req = AccountSubscribe(pubkey.to_solders(), config, req_id)
        await self.send_data(req)

    async def account_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from account notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = AccountUnsubscribe(subscription, req_id)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def logs_subscribe(
        self,
        filter_: Union[RpcTransactionLogsFilter, RpcTransactionLogsFilterMentions] = RpcTransactionLogsFilter.All,
        commitment: Optional[Commitment] = None,
    ) -> None:
        """Subscribe to transaction logging.

        Args:
            filter_: filter criteria for the logs.
            commitment: The commitment level to use.
        """
        req_id = self.increment_counter_and_get_id()
        commitment_to_use = None if commitment is None else _COMMITMENT_TO_SOLDERS[commitment]
        config = RpcTransactionLogsConfig(commitment_to_use)
        req = LogsSubscribe(filter_, config, req_id)
        await self.send_data(req)

    async def logs_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from transaction logging.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = LogsUnsubscribe(subscription, req_id)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def program_subscribe(  # pylint: disable=too-many-arguments
        self,
        program_id: PublicKey,
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
        data_slice: Optional[types.DataSliceOpts] = None,
        filters: Optional[Sequence[Union[int, types.MemcmpOpts]]] = None,
    ) -> None:
        """Receive notifications when the lamports or data for a given account owned by the program changes.

        Args:
            program_id: The program ID.
            commitment: Commitment level to use.
            encoding: Encoding to use.
            data_slice: (optional) Limit the returned account data using the provided `offset`: <usize> and
            `   length`: <usize> fields; only available for "base58" or "base64" encoding.
            filters: (optional) Options to compare a provided series of bytes with program account data at a particular offset.
                Note: an int entry is converted to a `dataSize` filter.
        """  # noqa: E501 # pylint: disable=line-too-long
        req_id = self.increment_counter_and_get_id()
        if commitment is None and encoding is None and data_slice is None and filters is None:
            config = None
        else:
            encoding_to_use = None if encoding is None else _ACCOUNT_ENCODING_TO_SOLDERS[encoding]
            commitment_to_use = None if commitment is None else _COMMITMENT_TO_SOLDERS[commitment]
            data_slice_to_use = (
                None if data_slice is None else UiDataSliceConfig(offset=data_slice.offset, length=data_slice.length)
            )
            account_config = RpcAccountInfoConfig(
                encoding=encoding_to_use, commitment=commitment_to_use, data_slice=data_slice_to_use
            )
            filters_to_use: Optional[List[Union[int, Memcmp]]] = (
                None if filters is None else [x if isinstance(x, int) else Memcmp(*x) for x in filters]
            )
            config = RpcProgramAccountsConfig(account_config, filters_to_use)
        req = ProgramSubscribe(program_id.to_solders(), config, req_id)
        await self.send_data(req)

    async def program_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from program account notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = ProgramUnsubscribe(subscription, req_id)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def signature_subscribe(
        self,
        signature: Signature,
        commitment: Optional[Commitment] = None,
    ) -> None:
        """Subscribe to a transaction signature to receive notification when the transaction is confirmed.

        Args:
            signature: The transaction signature to subscribe to.
            commitment: Commitment level.
        """
        req_id = self.increment_counter_and_get_id()
        commitment_to_use = None if commitment is None else _COMMITMENT_TO_SOLDERS[commitment]
        config = None if commitment_to_use is None else RpcSignatureSubscribeConfig(commitment=commitment_to_use)
        req = SignatureSubscribe(signature, config, req_id)
        await self.send_data(req)

    async def signature_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from signature notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = SignatureUnsubscribe(subscription, req_id)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def slot_subscribe(self) -> None:
        """Subscribe to receive notification anytime a slot is processed by the validator."""
        req_id = self.increment_counter_and_get_id()
        req = SlotSubscribe(req_id)
        await self.send_data(req)

    async def slot_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from slot notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = SlotUnsubscribe(subscription, req_id)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def slots_updates_subscribe(self) -> None:
        """Subscribe to receive a notification from the validator on a variety of updates on every slot."""
        req_id = self.increment_counter_and_get_id()
        req = SlotsUpdatesSubscribe(req_id)
        await self.send_data(req)

    async def slots_updates_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from slot update notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = SlotsUpdatesUnsubscribe(subscription, req_id)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def root_subscribe(self) -> None:
        """Subscribe to receive notification anytime a new root is set by the validator."""
        req_id = self.increment_counter_and_get_id()
        req = RootSubscribe(req_id)
        await self.send_data(req)

    async def root_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from root notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = RootUnsubscribe(subscription, req_id)
        await self.send_data(req)
        del self.subscriptions[subscription]

    async def vote_subscribe(self) -> None:
        """Subscribe to receive notification anytime a new vote is observed in gossip."""
        req_id = self.increment_counter_and_get_id()
        req = VoteSubscribe(req_id)
        await self.send_data(req)

    async def vote_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        """Unsubscribe from vote notifications.

        Args:
            subscription: ID of subscription to cancel.
        """
        req_id = self.increment_counter_and_get_id()
        req = VoteUnsubscribe(subscription, req_id)
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
