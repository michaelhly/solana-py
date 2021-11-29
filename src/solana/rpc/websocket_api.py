from typing import Union, Dict, Any, List, Optional
from json import loads, dumps
from websockets import connect, WebSocketClientProtocol
from jsonrpcserver.dispatcher import create_request
from jsonrpcclient import parse, Error, Ok
from apischema import deserialize

from solana.rpc.request_builder import RequestBody
from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solana.rpc.responses import (
    AccountNotification,
    LogsNotification,
    SubscriptionNotification,
    ProgramNotification,
    SignatureNotification,
    SlotNotification,
    RootNotification,
)
from solana.rpc.request_builder import AccountSubscribe, AccountUnsubscribe

_NOTIFICATION_MAP = {
    "accountNotification": AccountNotification,
    "logsNotification": LogsNotification,
    "programNotification": ProgramNotification,
    "signatureNotification": SignatureNotification,
    "slotNotification": SlotNotification,
    "rootNotification": RootNotification,
}


class SubscriptionError(Exception):
    """Raise when subscribing to an RPC feed fails."""


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

    async def recv(self) -> Union[SubscriptionNotification, Error, Ok]:
        data = await super().recv()
        as_json = loads(data)
        if isinstance(as_json, list):
            return [self._process_rpc_response(item) for item in as_json]
        return self._process_rpc_response(as_json)

    async def account_subscribe(
        self, pubkey: PublicKey, commitment: Optional[Commitment] = None, encoding: Optional[str] = None
    ):
        req = AccountSubscribe(pubkey, commitment, encoding)
        await self.send(req)

    async def account_unsubscribe(
        self,
        subscription: int,
    ):
        req = AccountUnsubscribe(subscription)
        await self.send(req)
        del self.subscriptions[subscription]

    def _process_rpc_response(self, data: dict) -> Union[SubscriptionNotification, Error, Ok]:
        parsed = _parse_rpc_response(data)
        if isinstance(parsed, Error):
            subscription = self.sent_subscriptions[parsed.id]
            self.failed_subscriptions[parsed.id] = subscription
            raise SubscriptionError(parsed, subscription)
        parsed_result = parsed.result
        if type(parsed_result) is int:
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
