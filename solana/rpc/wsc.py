"""API WebSocket Client to interact with the Solana JSON RPC Endpoint."""
from __future__ import annotations

from typing import Union

from solana.publickey import PublicKey

from .providers.ws import Provider
from .types import RPCMethod, RPCResponse


class WebSocketClient:
    """Websocket client class."""

    def __init__(self, endpoint: str):
        """Init API client for websocket."""
        self._provider = Provider(endpoint)

    def account_subscribe(self, pubkey: Union[PublicKey, str]) -> RPCResponse:
        """Subscribe to an account to receive when lamports change.

        param pubkey: Pubkey of account to receive lamports, as base-58 encoded string or public key object.

        >>> from solana.publickey import PublicKey
        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.account_subscribe(PublicKey(1)) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("accountSubscribe"), str(pubkey))

    def account_unsubscribe(self, account_id: int) -> RPCResponse:
        """Unsubscribe from account change notifications.

        param account_id: id of account Subscription to cancel

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> out = solana_client.account_subscribe(PublicKey(1))
        >>> account_id = out['result']
        >>> solana_client.account_unsubscribe(account_id) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 3}
        """
        return self._provider.make_request(RPCMethod("accountUnsubscribe"), account_id)

    def program_subscribe(self, pubkey: Union[PublicKey, str]) -> RPCResponse:
        """Subscribe to a program to receive notifications when lamports or data changes.

        param pubkey: Pubkey of account to receive lamports, as base-58 encoded string or public key object.
        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.program_subscribe(PublicKey(1))
        {'jsonrpc': '2.0', 'result': 3, 'id': 4}
        """
        return self._provider.make_request(RPCMethod("programSubscribe"), str(pubkey))

    def program_unsubscribe(self, account_id: int) -> RPCResponse:
        """Unsubscribe from account change notifications.

        param account_id: id of account Subscription to cancel

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> out = solana_client.program_subscribe(PublicKey(1))
        >>> account_id = out['result']
        >>> solana_client.program_unsubscribe(account_id) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 6}
        """
        return self._provider.make_request(RPCMethod("programUnsubscribe"), account_id)

    def signature_subscribe(self, pubkey: Union[PublicKey, str]) -> RPCResponse:
        """Subscribe to a transaction signature to receive notification.

        param pubkey: Transaction Signature, as base-58 encoded string

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.signature_subscribe(
        ... '2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b') #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 5, 'id': 7}
        """
        return self._provider.make_request(RPCMethod("signatureSubscribe"), pubkey)

    def signature_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from signature confirmation notification.

        param account_id: id of Subscription to cancel

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> out = solana_client.signature_subscribe(
        ... '2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b')
        >>> id = out['result']
        >>> solana_client.signature_unsubscribe(id) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 9}
        """
        return self._provider.make_request(RPCMethod("signatureUnsubscribe"), subscription_id)
        # def get_account_info(self, pubkey: Union[PublicKey, str]) -> RPCResponse:
        # return self._provider.make_request(RPCMethod("getAccountInfo"), str(pubkey))
        # def get_account_info(self, pubkey: Union[PublicKey, str]) -> RPCResponse:
        # return self._provider.make_request(RPCMethod("getAccountInfo"), str(pubkey))

    def slot_subscribe(self) -> RPCResponse:
        """Subscribe to receive notification anytime a slot is processed by the validator.

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_cllient.slot_subscribe() #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 7, 'id': 10}
        """
        return self._provider.make_request(RPCMethod("slotSubscribe"))

    def slot_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from slot.

        param subscription_id: id of sub to cancel

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.slot_unsubscribe(solana_client.slot_subscribe()['result']) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 12}
        """
        return self._provider.make_request(RPCMethod("slotUnsubscribe"), subscription_id)

    def root_subscribe(self) -> RPCResponse:
        """Subscribe to receive notification anytime a new root is set by the validator.

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.root_subscribe() #doctest: +SKIP
            {'jsonrpc': '2.0', 'result': 8, 'id': 13}
        """
        return self._provider.make_request(RPCMethod("rootSubscribe"))

    def root_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from root notifications.

        param subscription_id: id of sub to cancel

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.root_unsubscribe(solana_client.root(subscribe)['result']) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 14}

        """
        return self._provider.make_request(RPCMethod("rootUnsubscribe"), subscription_id)

    def vote_subscribe(self) -> RPCResponse:
        """Subscribe to receive notification anytime a new vote is observed in gossip.

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.vote_subscribe() #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': True, 'id': 15}

        """
        return self._provider.make_request(RPCMethod("voteSubscribe"))

    def vote_unsubscribe(self, subscription_id: int) -> RPCResponse:
        """Unsubscribe from vote notifications.

        param subscription_id: id of sub to cancel

        >>> solana_client = WebSocketClient("ws://localhost:8900")
        >>> solana_client.vote_unsubscribe(solana_client.vote_subscribe()['result']) #doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 11, 'id': 17}
        """
        return self._provider.make_request(RPCMethod("voteUnsubscribe"), subscription_id)

    def is_connected(self) -> bool:
        """Health check.

        >>> solana_client = Client("http://localhost:8900")
        >>> solana_client.is_connected() # doctest: +SKIP
        True
        """
        return self._provider.is_connected()
