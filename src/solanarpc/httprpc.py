"""Client to interact with the Solana JSON RPC HTTP Endpoint."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, cast

from base58 import b58encode
import requests

from solanarpc._utils.encoding import FriendlyJsonSerde
from solanarpc.rpc_types import URI, RPCMethod, RPCResponse
from solanaweb3.account import Account
from solanaweb3.blockhash import Blockhash
from solanaweb3.publickey import PublicKey
from solanaweb3.transaction import Transaction


def get_default_endpoint() -> URI:
    """Get the default http rpc endpoint."""
    return URI(os.environ.get("SOLANAWEB3_HTTP_URI", "http://localhost:8899"))


class HTTPClient(FriendlyJsonSerde):
    """HTTP client interact with the http rpc endpoint."""

    logger = logging.getLogger("solanaweb3.rpc.httprpc.HTTPClient")

    def __init__(self, endpoint: Optional[str] = None):
        """Init HTTPClient."""
        self._req_counter = 0
        self.endpoint_uri = get_default_endpoint() if not endpoint else URI(endpoint)

    def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make an HTTP reqeust to the http rpc endpoint."""
        self._req_counter += 1
        self.logger.debug(
            "Making HTTP request. RequestID: %d, URI: %s, Method: %s, Params: %s",
            self._req_counter,
            self.endpoint_uri,
            method,
            params,
        )
        headers = {"Content-Type": "application/json"}
        data = self.json_encode({"jsonrpc": "2.0", "id": self._req_counter, "method": method, "params": params})
        raw_response = requests.post(self.endpoint_uri, headers=headers, data=data)
        raw_response.raise_for_status()
        self.logger.debug(
            "Getting response HTTP. URI: %s, " "Method: %s, Response: %s", self.endpoint_uri, method, raw_response.text
        )
        return cast(RPCResponse, self.json_decode(raw_response.text))

    def get_balance(self, pubkey: PublicKey) -> RPCResponse:
        """Returns the balance of the account of provided Pubkey.

        :param pubkey: Pubkey of account to query, as base-58 encoded string.
        """
        return self.make_request(RPCMethod("getBalance"), str(pubkey))

    def get_confirmed_transaction(self, tx_sig: str, encoding: str = "json") -> RPCResponse:
        """Returns transaction details for a confirmed transaction.

        :param tx_sig: Transaction signature as base-58 encoded string N encoding attempts to use program-specific
        instruction parsers to return more human-readable and explicit data in the `transaction.message.instructions`
        list.
        """
        return self.make_request(RPCMethod("getConfirmedTransaction"), tx_sig, encoding)

    def get_recent_blockhash(self) -> RPCResponse:
        """Returns a recent block hash from the ledger.

        Response also includes a fee schedule that can be used to compute the cost
        of submitting a transaction using it.
        """
        return self.make_request(RPCMethod("getRecentBlockhash"))

    def request_airdrop(self, pubkey: PublicKey, lamports: int) -> RPCResponse:
        """Requests an airdrop of lamports to a Pubkey.

        :param pubkey: Pubkey of account to receive lamports, as base-58 encoded string.
        :param lamports: Amout of lamports.
        """
        return self.make_request(RPCMethod("requestAirdrop"), str(pubkey), lamports)

    def send_raw_transaction(self, txn: Transaction) -> RPCResponse:
        """Send a transaction that has already been signed and serialized into the wire format.

        :param txn: Fully-signed Transaction.
        """
        wire_format = b58encode(txn.serialize()).decode("utf-8")
        return self.make_request(RPCMethod("sendTransaction"), wire_format)

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
        return self.make_request(RPCMethod("sendTransaction"), wire_format)
