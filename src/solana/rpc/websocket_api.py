from typing import Union
from json import loads
from websockets import connect, WebSocketClientProtocol
from jsonrpcserver.dispatcher import create_request
from jsonrpcclient import parse, Error, Ok
from apischema import deserialize

from solana.rpc.responses import (
    AccountNotification,
    LogsNotification,
    SubscriptionNotification,
    ProgramNotification,
    SignatureNotification,
    SlotNotification,
    RootNotification,
)

_NOTIFICATION_MAP = {
    "accountNotification": AccountNotification,
    "logsNotification": LogsNotification,
    "programNotification": ProgramNotification,
    "signatureNotification": SignatureNotification,
    "slotNotification": SlotNotification,
    "rootNotification": RootNotification,
}


class SolanaWsClientProtocol(WebSocketClientProtocol):
    async def recv(self) -> Union[dict, list]:
        data = await super().recv()
        asjson = loads(data)
        if isinstance(asjson, list):
            return [_parse_rpc_response(item) for item in asjson]
        return _parse_rpc_response(asjson)


def _parse_rpc_response(data: dict) -> Union[SubscriptionNotification, Error, Ok]:
    if "params" in data:
        req = create_request(data)
        dtype = _NOTIFICATION_MAP[req.method]
        return deserialize(dtype, req.params)
    return parse(data)


class WebsocketClient(connect):
    def __init__(self, uri: str) -> None:
        super().__init__(uri, create_protocol=SolanaWsClientProtocol)

    # async def __aenter__(self) -> "WebsocketClient":
    #     """Use as a context manager."""
    #     await self._ws.__aenter__()
    #     return self

    # async def __aexit__(self, _exc_type, _exc, _tb):
    #     """Exits the context manager."""
    #     await self.close()

    # async def close(self) -> None:
    #     """Use this when you are done with the client."""
    #     await self._ws.protocol.close()

    # async def recv(self) -> Data:
    #     data = await super().recv()
    #     return data

    # async def send(self, message: Union[Data, Iterable[Data], AsyncIterable[Data]]) -> None:
    #     msg = message
    #     await super().send(msg)
