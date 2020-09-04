"""API WebSocket Client to interact with the Solana JSON RPC Endpoint."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from websockets import WebSocketClientProtocol  # type: ignore

from solana.publickey import PublicKey

from .commitment import Commitment, Max
from .providers.ws import WSProvider
from .types import RPCMethod, RPCResponse


class WebSocketClient:
    """Websocket client class."""

    _comm_key = "commitment"
    _encoding_key = "encoding"
    _data_slice_key = "dataSlice"
    _filters_key = "filters"

    def __init__(self, endpoint: str):
        """Init API client for websocket."""
        self._provider = WSProvider(endpoint)
        self._conn = self._provider.conn.ws

    def connection(self) -> Optional[WebSocketClientProtocol]:
        """Get the ws connection."""
        return self._provider.connection()

    def account_subscribe(
        self,
        pubkey: Union[PublicKey, str],
        commitment: Commitment = Max,
        encoding: str = "base64",
    ) -> RPCResponse:
        """Subscribe to an account to receive when lamports change.

        :param pubkey: Pubkey of account to receive lamports, as base-58 encoded string or public key object.
        :param encoding: (optional) encoding for the returned Transaction, either jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is base64. JSON is unstable.
        :param commitment: Commitment hyperlink: `Commitment
        <https://docs.solana.com/apps/jsonrpc-api#configuring-state-commitment>`_.

        >>> from solana.publickey import PublicKey #doctest: +SKIP
        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.account_subscribe(PublicKey(1)) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1, 'id': 1}
        """
        opts: Dict[str, Any] = {self._encoding_key: encoding, self._comm_key: commitment}
        return self._provider.make_request(RPCMethod("accountSubscribe"), str(pubkey), opts)

    def account_unsubscribe(self, account_id: int) -> RPCResponse:
        """Unsubscribe from account change notifications.

        :param account_id: id of account Subscription to cancel

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> resp = ws_client.account_subscribe(PublicKey(1)) #doctest: +SKIP
        >>> account_id = resp['result'] #doctest: +SKIP
        >>> ws_client.account_unsubscribe(account_id) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 3}
        """
        return self._provider.make_request(RPCMethod("accountUnsubscribe"), account_id)

    def program_subscribe(
        self,
        pubkey: Union[PublicKey, str],
        commitment: Commitment = Max,
        encoding: str = "base64",
        filters: List[str] = None,
    ) -> RPCResponse:
        """Subscribe to a program to receive notifications when lamports or data changes.

        :param pubkey: Pubkey of account to receive lamports, as base-58 encoded string or public key object.
        :param encoding: (optional) encoding for the returned Transaction, either jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is base64.
        :param filters: (optional) filter results using various filter objects.
        Account must meet all filter criteria to be included in results
        :param commitment: Commitment hyperlink: `Commitment
        <https://docs.solana.com/apps/jsonrpc-api#configuring-state-commitment>`_.

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.program_subscribe(PublicKey(1)) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 3, 'id': 4}
        """
        opts: Dict[str, Any] = {self._encoding_key: encoding, self._comm_key: commitment, self._filters_key: []}
        if filters:
            opts[self._filters_key].append(filters)
        return self._provider.make_request(RPCMethod("programSubscribe"), str(pubkey), opts)

    def program_unsubscribe(self, account_id: int) -> RPCResponse:
        """Unsubscribe from account change notifications.

        :param account_id: id of account Subscription to cancel

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> resp = ws_client.program_subscribe(PublicKey(1)) #doctest: +SKIP
        >>> account_id = resp['result'] #doctest: +SKIP
        >>> ws_client.program_unsubscribe(account_id) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 6}
        """
        return self._provider.make_request(RPCMethod("programUnsubscribe"), account_id)

    def signature_subscribe(
        self,
        pubkey: Union[PublicKey, str],
        commitment: Commitment = Max,
    ) -> RPCResponse:
        """Subscribe to a transaction signature to receive notification.

        :param pubkey: Transaction Signature, as base-58 encoded string
        :param commitment: Commitment hyperlink: `Commitment
        <https://docs.solana.com/apps/jsonrpc-api#configuring-state-commitment>`_.

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.signature_subscribe(  #doctest: +SKIP
        ... '2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b') #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 5, 'id': 7}
        """
        opts: Dict[str, Any] = {self._comm_key: commitment}
        return self._provider.make_request(RPCMethod("signatureSubscribe"), pubkey, opts)

    def signature_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from signature confirmation notification.

        :param account_id: id of Subscription to cancel

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> resp = ws_client.signature_subscribe(
        ... '2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b') #doctest: +SKIP
        >>> id = resp['result'] #doctest: +SKIP
        >>> ws_client.signature_unsubscribe(id) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 9}
        """
        return self._provider.make_request(RPCMethod("signatureUnsubscribe"), subscription_id)

    def slot_subscribe(self) -> RPCResponse:
        """Subscribe to receive notification anytime a slot is processed by the validator.

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.slot_subscribe() #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 7, 'id': 10}
        """
        return self._provider.make_request(RPCMethod("slotSubscribe"))

    def slot_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from slot.

        :param subscription_id: id of sub to cancel

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.slot_unsubscribe(ws_client.slot_subscribe()['result']) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 12}
        """
        return self._provider.make_request(RPCMethod("slotUnsubscribe"), subscription_id)

    def root_subscribe(self) -> RPCResponse:
        """Subscribe to receive notification anytime a new root is set by the validator.

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.root_subscribe() #doctest: +SKIP
            {'jsonrpc': '2.0', 'result': 8, 'id': 13}
        """
        return self._provider.make_request(RPCMethod("rootSubscribe"))

    def root_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from root notifications.

        :param subscription_id: id of sub to cancel

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.root_unsubscribe(ws_client.root(subscribe)['result']) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 14}

        """
        return self._provider.make_request(RPCMethod("rootUnsubscribe"), subscription_id)

    def vote_subscribe(self) -> RPCResponse:
        """Subscribe to receive notification anytime a new vote is observed in gossip.

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.vote_subscribe() #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 15}

        """
        return self._provider.make_request(RPCMethod("voteSubscribe"))

    def vote_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from vote notifications.

        :param subscription_id: id of sub to cancel

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.vote_unsubscribe(ws_client.vote_subscribe()['result']) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 11, 'id': 17}
        """
        return self._provider.make_request(RPCMethod("voteUnsubscribe"), subscription_id)

    def is_connected(self) -> bool:
        """Health check.

        >>> ws_client = WebSocketClient("ws://localhost:8900") #doctest: +SKIP
        >>> ws_client.is_connected() #doctest: +SKIP
        True
        """
        return self._provider.is_connected()
