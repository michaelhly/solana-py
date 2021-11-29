from typing import Union, Dict, Any, List, Optional
from json import loads, dumps
from websockets import connect, WebSocketClientProtocol
from jsonrpcserver.dispatcher import create_request
from jsonrpcclient import parse, Error, Ok
from apischema import deserialize

from solana.rpc.request_builder import RequestBody
from solana.publickey import PublicKey
from solana.transaction import TransactionSignature
from solana.rpc.commitment import Commitment
from solana.rpc import types
from solana.rpc.responses import (
    AccountNotification,
    LogsNotification,
    SubscriptionNotification,
    ProgramNotification,
    SignatureNotification,
    SlotNotification,
    RootNotification,
    SlotsUpdatesNotification,
)
from solana.rpc.request_builder import (
    AccountSubscribe,
    AccountUnsubscribe,
    LogsSubscribe,
    LogsUnsubscribe,
    LogsSubsrcibeFilter,
    MentionsFilter,
    ProgramSubscribe,
    ProgramUnsubscribe,
    SignatureSubscribe,
    SignatureUnsubscribe,
    SlotSubscribe,
    SlotUnsubscribe,
    SlotsUpdatesSubscribe,
    SlotsUpdatesUnsubscribe,
    RootSubscribe,
    RootUnsubscribe,
    VoteSubscribe,
    VoteUnsubscribe,
)

_NOTIFICATION_MAP = {
    "accountNotification": AccountNotification,
    "logsNotification": LogsNotification,
    "programNotification": ProgramNotification,
    "signatureNotification": SignatureNotification,
    "slotNotification": SlotNotification,
    "rootNotification": RootNotification,
    "slotsUpdatesNotification": SlotsUpdatesNotification,
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
    def __init__(self, *args, **kwargs):
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

    async def send(self, data: Union[RequestBody, List[RequestBody]]) -> None:
        if isinstance(data, RequestBody):
            to_send = data.to_request()
        else:
            to_send = [d.to_request() for d in data]
        await self._send(to_send)

    async def recv(
        self,
    ) -> Union[List[Union[SubscriptionNotification, Error, Ok]], SubscriptionNotification, Error, Ok]:
        data = await super().recv()
        as_json = loads(data)
        if isinstance(as_json, list):
            return [self._process_rpc_response(item) for item in as_json]
        return self._process_rpc_response(as_json)

    async def account_subscribe(
        self, pubkey: PublicKey, commitment: Optional[Commitment] = None, encoding: Optional[str] = None
    ) -> None:
        req = AccountSubscribe(pubkey, commitment, encoding)
        await self.send(req)

    async def account_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = AccountUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    async def logs_subscribe(
        self,
        filter_: Union[str, MentionsFilter] = LogsSubsrcibeFilter.ALL,
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
    ) -> None:
        req = LogsSubscribe(filter_, commitment, encoding)
        await self.send(req)

    async def logs_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = LogsUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    async def program_subscribe(
        self,
        program_id: PublicKey,
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
        data_size: Optional[int] = None,
        memcmp_opts: Optional[List[types.MemcmpOpts]] = None,
    ) -> None:
        req = ProgramSubscribe(program_id, commitment, encoding, data_size, memcmp_opts)
        await self.send(req)

    async def program_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = ProgramUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    async def signature_subscribe(
        self,
        signature: TransactionSignature,
        commitment: Optional[Commitment] = None,
    ) -> None:
        req = SignatureSubscribe(signature, commitment)
        await self.send(req)

    async def signature_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = SignatureUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    async def slot_subscribe(self) -> None:
        req = SlotSubscribe()
        await self.send(req)

    async def slot_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = SlotUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    async def slots_updates_subscribe(self) -> None:
        req = SlotsUpdatesSubscribe()
        await self.send(req)

    async def slots_updates_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = SlotsUpdatesUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    async def root_subscribe(self) -> None:
        req = RootSubscribe()
        await self.send(req)

    async def root_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = RootUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    async def vote_subscribe(self) -> None:
        req = VoteSubscribe()
        await self.send(req)

    async def vote_unsubscribe(
        self,
        subscription: int,
    ) -> None:
        req = VoteUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    def _process_rpc_response(self, data: dict) -> Union[SubscriptionNotification, Error, Ok]:
        parsed = _parse_rpc_response(data)
        if isinstance(parsed, Error):
            subscription = self.sent_subscriptions[parsed.id]
            self.failed_subscriptions[parsed.id] = subscription
            raise SubscriptionError(parsed, subscription)
        parsed_result = parsed.result
        if type(parsed_result) is int and type(parsed) is Ok:
            self.subscriptions[parsed_result] = self.sent_subscriptions[parsed.id]
        return parsed


def _parse_rpc_response(data: dict) -> Union[SubscriptionNotification, Error, Ok]:
    if "params" in data:
        req = create_request(data)
        dtype = _NOTIFICATION_MAP[req.method]
        return deserialize(dtype, req.params)
    return parse(data)


class WebsocketClient(connect):
    def __init__(self, uri: str = "ws://127.0.0.1:8900") -> None:
        super().__init__(uri, create_protocol=SolanaWsClientProtocol)
