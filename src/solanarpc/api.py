"""Client to interact with the Solana JSON RPC Endpoint."""
from __future__ import annotations

from typing import Optional

from base58 import b58encode

from solanaweb3.account import Account
from solanaweb3.blockhash import Blockhash
from solanaweb3.publickey import PublicKey
from solanaweb3.transaction import Transaction

from .rpc_types import RPCMethod, RPCResponse
from .providers import http

# Endpoint types
HTTP = "http"
WEBSOCKET = "ws"


class Client:
    """RPC Client interact with the Solana RPC API."""

    def __init__(self, endpoint: Optional[str] = None, endpoint_type: Optional[str] = None):
        """Init API client.

        :param endpoint: RPC endpoint to connect to.
        :param endpoint_type: Type of RPC endpoint.
            - "http" for HTTP endpoint.
            - "ws" for webscoket endpoint.
        """
        if endpoint_type == WEBSOCKET:
            raise NotImplementedError("websocket RPC is currently not supported")
        else:
            # Default to http provider, if not endpoint type is provided.
            self._provider = http.HTTPProvider(endpoint)

    def is_connected(self) -> bool:
        """Health check."""
        return self._provider.is_connected()

    def get_balance(self, pubkey: PublicKey) -> RPCResponse:
        """Returns the balance of the account of provided Pubkey.

        :param pubkey: Pubkey of account to query, as base-58 encoded string.
        """
        return self._provider.make_request(RPCMethod("getBalance"), str(pubkey))

    def get_confirmed_transaction(self, tx_sig: str, encoding: str = "json") -> RPCResponse:
        """Returns transaction details for a confirmed transaction.

        :param tx_sig: Transaction signature as base-58 encoded string N encoding attempts to use program-specific
        instruction parsers to return more human-readable and explicit data in the `transaction.message.instructions`
        list.
        """
        return self._provider.make_request(RPCMethod("getConfirmedTransaction"), tx_sig, encoding)

    def get_recent_blockhash(self) -> RPCResponse:
        """Returns a recent block hash from the ledger.

        Response also includes a fee schedule that can be used to compute the cost
        of submitting a transaction using it.
        """
        return self._provider.make_request(RPCMethod("getRecentBlockhash"))

    def request_airdrop(self, pubkey: PublicKey, lamports: int) -> RPCResponse:
        """Requests an airdrop of lamports to a Pubkey.

        :param pubkey: Pubkey of account to receive lamports, as base-58 encoded string.
        :param lamports: Amout of lamports.
        """
        return self._provider.make_request(RPCMethod("requestAirdrop"), str(pubkey), lamports)

    def send_raw_transaction(self, txn: Transaction) -> RPCResponse:
        """Send a transaction that has already been signed and serialized into the wire format.

        :param txn: Fully-signed Transaction.
        """
        wire_format = b58encode(txn.serialize()).decode("utf-8")
        return self._provider.make_request(RPCMethod("sendTransaction"), wire_format)

    def send_transaction(self, txn: Transaction, *signers: Account) -> RPCResponse:
        """Send a transaction.

        :param txn: Fully-signed Transaction.
        :param signers: Signers to sign the transaction.
        """
        try:
            # TODO: Cache recent blockhash
            blockhash_resp = self.get_recent_blockhash()
            if not blockhash_resp["result"]:
                raise RuntimeError("failed to get recent blockhash")
            txn.recent_blockhash = Blockhash(blockhash_resp["result"]["value"]["blockhash"])
        except Exception as err:
            raise RuntimeError("failed to get recent blockhash") from err

        txn.sign(*signers)
        wire_format = b58encode(txn.serialize()).decode("utf-8")
        return self._provider.make_request(RPCMethod("sendTransaction"), wire_format)
