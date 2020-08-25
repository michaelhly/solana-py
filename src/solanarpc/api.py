"""Client to interact with the Solana JSON RPC Endpoint."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from base58 import b58decode, b58encode

from solanaweb3.account import Account
from solanaweb3.blockhash import Blockhash
from solanaweb3.publickey import PublicKey
from solanaweb3.transaction import Transaction

from .providers import http
from .rpc_types import RPCMethod, RPCResponse

# Client types
HTTP = "http"
WEBSOCKET = "ws"


class Client:  # pylint: disable=too-many-public-methods
    """RPC Client interact with the Solana RPC API."""

    def __init__(self, endpoint: Optional[str] = None, client_type: Optional[str] = None):
        """Init API client.

        :param endpoint: RPC endpoint to connect to.
        :param client_type: Type of RPC client.
            - "http" for HTTP endpoint.
            - "ws" for webscoket endpoint.
        """
        if client_type == WEBSOCKET:
            self._type = WEBSOCKET
            raise NotImplementedError("websocket RPC is currently not supported")
        else:
            # Default to http provider, if no endpoint type is provided.
            self._type = HTTP
            self._provider = http.HTTPProvider(endpoint)

    def is_connected(self) -> bool:
        """Health check."""
        return self._provider.is_connected()

    def get_balance(self, pubkey: PublicKey) -> RPCResponse:
        """Returns the balance of the account of provided Pubkey.

        :param pubkey: Pubkey of account to query, as base-58 encoded string.
        """
        return self._provider.make_request(RPCMethod("getBalance"), str(pubkey))

    def get_block_time(self, slot: int) -> RPCResponse:
        """Fetch the estimated production time of a block.

        :param slot: Block, identified by Slot .
        """
        return self._provider.make_request(RPCMethod("getBlockTime"), slot)

    def get_cluster_nodes(self) -> RPCResponse:
        """Returns information about all the nodes participating in the cluster."""
        return self._provider.make_request(RPCMethod("getClusterNodes"))

    def get_confirmed_block(self, slot: int, encoding: str = "json",) -> RPCResponse:
        """Returns identity and transaction information about a confirmed block in the ledger.

        :param slot: start_slot, as u64 integer.
        :param encoding: (optional) encoding for the returned Transaction, either "json", "jsonParsed",
        "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.
        """
        return self._provider.make_request(RPCMethod("getConfirmedBlock"), slot, encoding)

    def get_confirmed_blocks(self, start_slot: int, end_slot: Optional[int] = None) -> RPCResponse:
        """Returns identity and transaction information about a confirmed block in the ledger.

        :param start_slot: start_slot, as u64 integer.
        :param end_slot: (optional) encoding for the returned Transaction, either "json", "jsonParsed",
        "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.
        """
        if end_slot:
            return self._provider.make_request(RPCMethod("getConfirmedBlock"), start_slot, end_slot)
        return self._provider.make_request(RPCMethod("getConfirmedBlock"), start_slot)

    def get_confirmed_signature_for_address2(
        self, account: Union[str, Account, PublicKey], before: Optional[str] = None, limit: Optional[int] = None
    ) -> RPCResponse:
        """Returns confirmed signatures for transactions involving an address.

        Signatures are returned backwards in time from the provided signature or
        most recent confirmed block.

        :param account: Account to be queried.
        :param before: (optional) start searching backwards from this transaction signature.
        If not provided the search starts from the top of the highest max confirmed block.
        :param limit: (optoinal) maximum transaction signatures to return (between 1 and 1,000, default: 1,000).
        """
        opts: Dict[str, Union[int, str]] = {}
        if before:
            opts["before"] = before
        if limit:
            opts["limit"] = limit

        if isinstance(account, Account):
            account = str(account.public_key())
        if isinstance(account, PublicKey):
            account = str(account)

        return self._provider.make_request(RPCMethod("getConfirmedSignaturesForAddress2"), account, opts)

    def get_confirmed_transaction(self, tx_sig: str, encoding: str = "json") -> RPCResponse:
        """Returns transaction details for a confirmed transaction.

        :param tx_sig: Transaction signature as base-58 encoded string N encoding attempts to use program-specific
        instruction parsers to return more human-readable and explicit data in the `transaction.message.instructions`
        list.
        :param encoding: (optional) encoding for the returned Transaction, either "json", "jsonParsed",
        "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.
        """
        return self._provider.make_request(RPCMethod("getConfirmedTransaction"), tx_sig, encoding)

    def get_epoch_info(self) -> RPCResponse:
        """Returns information about the current epoch."""
        return self._provider.make_request(RPCMethod("getEpochInfo"))

    def get_epoch_schedule(self) -> RPCResponse:
        """Returns epoch schedule information from this cluster's genesis config."""
        return self._provider.make_request(RPCMethod("getEpochSchedule"))

    def get_fee_calculator_for_blockhash(self, blockhash: Union[str, Blockhash]) -> RPCResponse:
        """Returns the fee calculator associated with the query blockhash, or null if the blockhash has expired.

        :param blockhash: Blockhash to query.
        """
        blockhash = b58encode(blockhash).decode("utf-8")
        return self._provider.make_request(RPCMethod("getFeeCalculatorForBlockhash"), blockhash)

    def get_fee_rate_governor(self) -> RPCResponse:
        """Returns the fee rate governor information from the root bank."""
        return self._provider.make_request(RPCMethod("getFeeRateGovernor"))

    def get_fees(self) -> RPCResponse:
        """Returns a recent block hash from the ledger, a fee schedule and the last slot the blockhash will be valid."""
        return self._provider.make_request(RPCMethod("getFee"))

    def get_first_available_block(self) -> RPCResponse:
        """Returns the slot of the lowest confirmed block that has not been purged from the ledger."""
        return self._provider.make_request(RPCMethod("getFirstAvailableBlock"))

    def get_genesis_hash(self) -> RPCResponse:
        """Returns the genesis hash."""
        return self._provider.make_request(RPCMethod("getGenesisHash"))

    def get_identity(self) -> RPCResponse:
        """Returns the identity pubkey for the current node."""
        return self._provider.make_request(RPCMethod("getIdentity"))

    def get_inflation_governor(self) -> RPCResponse:
        """Returns the current inflation governor."""
        return self._provider.make_request(RPCMethod("getInflationGovernor"))

    def get_largest_accounts(self, filter_opt: Optional[str] = None) -> RPCResponse:
        """Returns the 20 largest accounts, by lamport balance.

        :param filter_opt: Filter results by account type; currently supported: circulating|nonCirculating.
        """
        opt: Dict[Optional[str], Optional[str]] = {"filter": filter_opt} if filter_opt else {}
        return self._provider.make_request(RPCMethod("getLargestAccounts"), opt)

    def get_leader_schedule(self, epoch: Optional[int] = None) -> RPCResponse:
        """Returns the leader schedule for an epoch.

        :param epoch: Fetch the leader schedule for the epoch that corresponds to the provided slot.
        If unspecified, the leader schedule for the current epoch is fetched.
        """
        if epoch:
            return self._provider.make_request(RPCMethod("getLeaderSchedule"), epoch)
        return self._provider.make_request(RPCMethod("getLeaderSchedule"))

    def get_minimum_balance_for_rent_exemption(self, usize: int) -> RPCResponse:
        """Returns minimum balance required to make account rent exempt.

        :param usize: Account data length.
        """
        return self._provider.make_request(RPCMethod("getMinimumBalanceForRentExemption"), usize)

    def get_program_accounts(
        self,
        pubkey: Union[str, PublicKey],
        encoding: Optional[str] = None,
        data_slice: Optional[int] = None,
        filter_opts: Optional[Dict] = None,
    ) -> RPCResponse:
        """Returns all accounts owned by the provided program Pubkey.

        :param pubkey: Pubkey of program, as base-58 encoded string or PublicKey object.
        :param encoding: (optional) encoding for the returned Transaction, either jsonParsed",
        "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.
        :param data_slice: limit the returned account data using the provided `offset`: <usize> and
        `length`: <usize> fields; only available for "base58" or "base64" encoding.
        :param filter_opts: filter results using various
        [filter objects](https://docs.solana.com/apps/jsonrpc-api#filters);
        account must meet all filter criteria to be included in results.
        """
        opts: Dict[str, List[Any]] = {"filters": []}
        if data_slice:
            opts["filters"].append({"dataSize": data_slice})
        if filter_opts:
            opts["filters"].append(filter_opts)
        if encoding:
            opts["encoding"].append(encoding)

        if isinstance(pubkey, PublicKey):
            pubkey = str(pubkey)

        return self._provider.make_request(RPCMethod("getProgramAccounts"), pubkey, opts)

    def get_recent_blockhash(self) -> RPCResponse:
        """Returns a recent block hash from the ledger.

        Response also includes a fee schedule that can be used to compute the cost
        of submitting a transaction using it.
        """
        return self._provider.make_request(RPCMethod("getRecentBlockhash"))

    def get_signature_statuses(
        self, signatures: List[Union[str, bytes]], search_transaction_history: bool = False
    ) -> RPCResponse:
        """Returns the statuses of a list of signatures.

        Unless the `searchTransactionHistory` configuration parameter is included, this method only
        searches the recent status cache of signatures, which retains statuses for all active slots plus
        `MAX_RECENT_BLOCKHASHES` rooted slots.

        :param signatures: An array of transaction signatures to confirm, as base-58 encoded strings.
        :param search_transaction_history: If true, a Solana node will search its ledger cache for
        any signatures not found in the recent status cache.
        """
        base58_sigs: List[str] = []
        for sig in signatures:
            if isinstance(sig, str):
                base58_sigs.append(b58encode(b58decode(sig)).decode("utf-8"))
            else:
                base58_sigs.append(b58encode(sig).decode("utf-8"))

        return self._provider.make_request(
            RPCMethod("getSignatureStatuses"), base58_sigs, {"searchTransactionHistory", search_transaction_history}
        )

    def get_slot(self) -> RPCResponse:
        """Returns the current slot the node is processing."""
        return self._provider.make_request(RPCMethod("getSlot"))

    def get_slot_leader(self) -> RPCResponse:
        """Returns the current slot leader."""
        return self._provider.make_request(RPCMethod("getSlotLeader"))

    def get_stake_activation(self, pubkey: Union[PublicKey, str], epoch: Optional[int] = None):
        """Returns epoch activation information for a stake account.

        :param pubkey: Pubkey of stake account to query, as base-58 encoded string or PublicKey object.
        :param epoch: (optional) epoch for which to calculate activation details. If parameter not provided,
        defaults to current epoch.
        """
        opts = {}
        if epoch:
            opts["epoch"] = epoch

        return self._provider.make_request(RPCMethod("getStakeActivation"), str(pubkey), opts)

    def get_supply(self) -> RPCResponse:
        """Returns information about the current supply."""
        return self._provider.make_request(RPCMethod("getSupply"))

    def get_token_account_balance(self, pubkey: Union[str, PublicKey]):
        """Returns the token balance of an SPL Token account (UNSTABLE).

        :param pubkey: Pubkey of Token account to query, as base-58 encoded string or PublicKey object.
        """
        return self._provider.make_request(RPCMethod("getTokenAccountBalance"), str(pubkey))

    def get_token_accounts_by_delegate(self) -> RPCResponse:
        """Returns all SPL Token accounts by approved Delegate (UNSTABLE)."""
        raise NotImplementedError("get_token_account_by_delegate not implemented")

    def get_token_accounts_by_owner(self) -> RPCResponse:
        """Returns all SPL Token accounts by token owner (UNSTABLE)."""
        raise NotImplementedError("get_token_account_by_owner not implemented")

    def get_token_largest_accounts(self, pubkey: Union[PublicKey, str]) -> RPCResponse:
        """Returns the 20 largest accounts of a particular SPL Token type (UNSTABLE)."""
        raise NotImplementedError("get_token_largbest_accounts not implemented")

    def get_token_supply(self, pubkey: Union[PublicKey, str]) -> RPCResponse:
        """Returns the total supply of an SPL Token type(UNSTABLE)."""
        raise NotImplementedError("get_token_supply not implemented")

    def get_transaction_count(self) -> RPCResponse:
        """Returns the current Transaction count from the ledger."""
        return self._provider.make_request(RPCMethod("getTransactionCount"))

    def get_minimum_ledger_slot(self) -> RPCResponse:
        """Returns the lowest slot that the node has information about in its ledger.

        This value may increase over time if the node is configured to purge older ledger data.
        """
        return self._provider.make_request(RPCMethod("minimumLedgerSlot"))

    def get_version(self) -> RPCResponse:
        """Returns the current solana versions running on the node."""
        return self._provider.make_request(RPCMethod("getVersion"))

    def request_airdrop(self, pubkey: Union[PublicKey, str], lamports: int) -> RPCResponse:
        """Requests an airdrop of lamports to a Pubkey.

        :param pubkey: Pubkey of account to receive lamports, as base-58 encoded string or public key object.
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

    def simulate_transaction(self, txn: Transaction, signer_verify: bool = False) -> RPCResponse:
        """Simulate sending a transaction.

        :param txn: Transaction, as base-58 encoded string.
        The transaction must have a valid blockhash, but is not required to be signed.
        :param signer_verify: if true the transaction signatures will be verified (default: false).
        """
        try:
            b58decode(str(txn.recent_blockhash))
        except Exception as err:
            raise ValueError("transaction must have a valid blockhash") from err

        wire_format = b58encode(txn.serialize()).decode("utf-8")
        return self._provider.make_request(
            RPCMethod("simulateTransaction"), wire_format, {"signerVerify": signer_verify}
        )

    def set_log_filter(self, log_filter: str) -> RPCResponse:
        """Sets the log filter on the validator.

        :param log_filter: The new log filter to use
        """
        return self._provider.make_request(RPCMethod("setLogFilter"), log_filter)

    def validator_exit(self) -> RPCResponse:
        """Request to have the validator exit.

        Validator must have booted with RPC exit enabled (`--enable-rpc-exit` parameter).
        """
        return self._provider.make_request(RPCMethod("validatorExit"))
