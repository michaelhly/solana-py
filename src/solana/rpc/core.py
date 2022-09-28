# pylint: disable=too-many-arguments
"""Helper code for api.py and async_api.py."""
from base64 import b64encode
from typing import Any, Dict, List, Optional, Tuple, Union, cast

try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal  # type: ignore

from based58 import b58decode, b58encode
from solders.rpc.requests import (
    GetBalance,
    GetAccountInfo,
    GetBlockCommitment,
    GetBlockTime,
    GetClusterNodes,
    GetBlock,
    GetBlockHeight,
    GetRecentPerformanceSamples,
    GetBlocks,
    GetSignaturesForAddress,
    GetTransaction,
    GetEpochInfo,
    GetFeeForMessage,
    GetInflationGovernor,
    GetLargestAccounts,
)
from solders.rpc.config import (
    RpcContextConfig,
    RpcAccountInfoConfig,
    UiDataSliceConfig,
    RpcBlockConfig,
    RpcSignaturesForAddressConfig,
    RpcTransactionConfig,
    RpcLargestAccountsFilter,
)
from solders.account_decoder import UiAccountEncoding
from solders.signature import Signature
from solders.commitment_config import CommitmentLevel

from solana.blockhash import Blockhash, BlockhashCache
from solana.message import Message
from solana.publickey import PublicKey
from solana.rpc import types
from solana.transaction import Transaction

from .commitment import Commitment, Finalized, Confirmed, Processed

_COMMITMENT_TO_SOLDERS = {
    Finalized: CommitmentLevel.Finalized,
    Confirmed: CommitmentLevel.Confirmed,
    Processed: CommitmentLevel.Processed,
}
_ENCODING_TO_SOLDERS = {
    "base58": UiAccountEncoding.Base58,
    "base64": UiAccountEncoding.Base64,
    "jsonParsed": UiAccountEncoding.JsonParsed,
    "base64+zstd": UiAccountEncoding.Base64Zstd,
}
_LARGEST_ACCOUNTS_FILTER_TO_SOLDERS = {
    "circulating": RpcLargestAccountsFilter.Circulating,
    "nonCirculating": RpcLargestAccountsFilter.NonCirculating,
}


class RPCException(Exception):
    """Raised when RPC method returns an error result."""


class RPCNoResultException(Exception):
    """Raised when an RPC method returns no result."""


class UnconfirmedTxError(Exception):
    """Raise when confirming a transaction times out."""


class TransactionExpiredBlockheightExceededError(Exception):
    """Raise when confirming an expired transaction that exceeded the blockheight."""


class TransactionUncompiledError(Exception):
    """Raise when transaction is not compiled to a message."""


class _ClientCore:  # pylint: disable=too-few-public-methods
    _comm_key = "commitment"
    _encoding_key = "encoding"
    _data_slice_key = "dataSlice"
    _skip_preflight_key = "skipPreflight"
    _preflight_comm_key = "preflightCommitment"
    _max_retries = "maxRetries"
    _before_rpc_config_key = "before"
    _limit_rpc_config_key = "limit"
    _until_rpc_config_key = "until"
    _get_cluster_nodes = GetClusterNodes()
    _get_epoch_schedule = types.RPCMethod("getEpochSchedule")
    _get_fee_rate_governor = types.RPCMethod("getFeeRateGovernor")
    _get_first_available_block = types.RPCMethod("getFirstAvailableBlock")
    _get_genesis_hash = types.RPCMethod("getGenesisHash")
    _get_identity = types.RPCMethod("getIdentity")
    _get_inflation_rate = types.RPCMethod("getInflationRate")
    _minimum_ledger_slot = types.RPCMethod("minimumLedgerSlot")
    _get_version = types.RPCMethod("getVersion")
    _validator_exit = types.RPCMethod("validatorExit")

    def __init__(self, commitment: Optional[Commitment] = None, blockhash_cache: Union[BlockhashCache, bool] = False):
        self._commitment = commitment or Finalized
        self.blockhash_cache: Union[BlockhashCache, Literal[False]] = (
            BlockhashCache()
            if blockhash_cache is True
            else cast(Union[BlockhashCache, Literal[False]], blockhash_cache)
        )

    @property
    def commitment(self) -> Commitment:
        """The default commitment used for requests."""
        return self._commitment

    def _get_balance_body(self, pubkey: PublicKey, commitment: Optional[Commitment]) -> GetBalance:
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        return GetBalance(pubkey.to_solders(), RpcContextConfig(commitment=commitment_to_use))

    def _get_account_info_body(
        self,
        pubkey: PublicKey,
        commitment: Optional[Commitment],
        encoding: str,
        data_slice: Optional[types.DataSliceOpts],
    ) -> Tuple[types.RPCMethod, str, Dict[str, Any]]:
        data_slice_to_use = (
            None if data_slice is None else UiDataSliceConfig(offset=data_slice.offset, length=data_slice.length)
        )
        encoding_to_use = _ENCODING_TO_SOLDERS[encoding]
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        config = RpcAccountInfoConfig(
            encoding=encoding_to_use, data_slice=data_slice_to_use, commitment=commitment_to_use
        )
        return GetAccountInfo(pubkey.to_solders(), config)

    @staticmethod
    def _get_block_commitment_body(slot: int) -> GetBlockCommitment:
        return GetBlockCommitment(slot)

    @staticmethod
    def _get_block_time_body(slot: int) -> GetBlockTime:
        return GetBlockTime(slot)

    @staticmethod
    def _get_block_body(slot: int, encoding: str) -> GetBlock:
        encoding_to_use = _ENCODING_TO_SOLDERS[encoding]
        config = RpcBlockConfig(encoding=encoding_to_use)
        return GetBlock(slot=slot, config=config)

    def _get_block_height_body(self, commitment: Optional[Commitment]) -> GetBlockHeight:
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        return GetBlockHeight(RpcContextConfig(commitment=commitment_to_use))

    @staticmethod
    def _get_recent_performance_samples_body(limit: Optional[int]) -> GetRecentPerformanceSamples:
        return GetRecentPerformanceSamples(limit)

    @staticmethod
    def _get_blocks_body(start_slot: int, end_slot: Optional[int]) -> GetBlocks:
        return GetBlocks(start_slot, end_slot)

    def _get_signatures_for_address_body(
        self,
        address: PublicKey,
        before: Optional[Signature],
        until: Optional[Signature],
        limit: Optional[Signature],
        commitment: Optional[Commitment],
    ) -> GetSignaturesForAddress:
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        config = RpcSignaturesForAddressConfig(before=before, until=until, limit=limit, commitment=commitment_to_use)
        return GetSignaturesForAddress(address.to_solders(), config)

    def _get_transaction_body(
        self, tx_sig: Signature, encoding: str = "json", commitment: Commitment = None
    ) -> GetTransaction:
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        encoding_to_use = _ENCODING_TO_SOLDERS[encoding]
        config = RpcTransactionConfig(encoding=encoding_to_use, commitment=commitment_to_use)
        return GetTransaction(tx_sig, config)

    def _get_epoch_info_body(self, commitment: Optional[Commitment]) -> GetEpochInfo:
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        config = RpcContextConfig(commitment=commitment_to_use)
        return GetEpochInfo(config)

    def _get_fee_for_message_body(self, message: Message, commitment: Optional[Commitment]) -> GetFeeForMessage:
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        return GetFeeForMessage(message.to_solders(), commitment_to_use)

    def _get_inflation_governor_body(self, commitment: Optional[Commitment]) -> GetInflationGovernor:
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        return GetInflationGovernor(commitment_to_use)

    def _get_largest_accounts_body(
        self, filter_opt: Optional[str], commitment: Optional[Commitment]
    ) -> GetLargestAccounts:
        filter_to_use = None if filter_opt else _LARGEST_ACCOUNTS_FILTER_TO_SOLDERS[filter_opt]
        commitment_to_use = _COMMITMENT_TO_SOLDERS[commitment or self._commitment]
        return GetLargestAccounts(commitment=commitment_to_use, filter_=filter_to_use)

    def _get_leader_schedule_body(
        self, epoch: Optional[int], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Optional[int], Dict[str, Commitment]]:
        return types.RPCMethod("getLeaderSchedule"), epoch, {self._comm_key: commitment or self._commitment}

    def _get_minimum_balance_for_rent_exemption_body(
        self, usize: int, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, int, Dict[str, Commitment]]:
        return (
            types.RPCMethod("getMinimumBalanceForRentExemption"),
            usize,
            {self._comm_key: commitment or self._commitment},
        )

    def _get_multiple_accounts_body(
        self,
        pubkeys: List[Union[PublicKey, str]],
        commitment: Optional[Commitment],
        encoding: str,
        data_slice: Optional[types.DataSliceOpts],
    ) -> Tuple[types.RPCMethod, List[str], Dict[str, Any]]:
        opts: Dict[str, Any] = {self._encoding_key: encoding, self._comm_key: commitment or self._commitment}
        if data_slice:
            opts[self._data_slice_key] = dict(data_slice._asdict())
        return types.RPCMethod("getMultipleAccounts"), [str(pubkey) for pubkey in pubkeys], opts

    def _get_program_accounts_body(
        self,
        pubkey: Union[str, PublicKey],
        commitment: Optional[Commitment],
        encoding: Optional[str],
        data_slice: Optional[types.DataSliceOpts],
        data_size: Optional[int],
        memcmp_opts: Optional[List[types.MemcmpOpts]],
    ) -> Tuple[types.RPCMethod, str, Dict[str, Any]]:  # pylint: disable=too-many-arguments
        opts: Dict[str, Any] = {"filters": []}
        for opt in [] if not memcmp_opts else memcmp_opts:
            opts["filters"].append({"memcmp": dict(opt._asdict())})
        if data_size:
            opts["filters"].append({"dataSize": data_size})
        if data_slice:
            opts[self._data_slice_key] = dict(data_slice._asdict())
        if encoding:
            opts[self._encoding_key] = encoding
        opts[self._comm_key] = commitment

        return types.RPCMethod("getProgramAccounts"), str(pubkey), opts

    def _get_recent_blockhash_body(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getRecentBlockhash"), {self._comm_key: commitment or self._commitment}

    def _get_latest_blockhash_body(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getLatestBlockhash"), {self._comm_key: commitment or self._commitment}

    @staticmethod
    def _get_signature_statuses_body(
        signatures: List[Union[str, bytes]], search_transaction_history: bool
    ) -> Tuple[types.RPCMethod, List[str], Dict[str, bool]]:
        base58_sigs: List[str] = []
        for sig in signatures:
            if isinstance(sig, str):
                base58_sigs.append(b58encode(b58decode(sig.encode("ascii"))).decode("utf-8"))
            else:
                base58_sigs.append(b58encode(sig).decode("utf-8"))

        return (
            types.RPCMethod("getSignatureStatuses"),
            base58_sigs,
            {"searchTransactionHistory": search_transaction_history},
        )

    def _get_slot_body(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getSlot"), {self._comm_key: commitment or self._commitment}

    def _get_slot_leader_body(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getSlotLeader"), {self._comm_key: commitment or self._commitment}

    def _get_stake_activation_body(
        self,
        pubkey: Union[PublicKey, str],
        epoch: Optional[int],
        commitment: Optional[Commitment],
    ) -> Tuple[types.RPCMethod, str, Dict[str, Union[int, Commitment]]]:
        opts: Dict[str, Union[int, Commitment]] = {self._comm_key: commitment or self._commitment}
        if epoch:
            opts["epoch"] = epoch

        return types.RPCMethod("getStakeActivation"), str(pubkey), opts

    def _get_supply_body(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getSupply"), {self._comm_key: commitment or self._commitment}

    def _get_token_account_balance_body(
        self, pubkey: Union[str, PublicKey], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Commitment]]:
        return types.RPCMethod("getTokenAccountBalance"), str(pubkey), {self._comm_key: commitment or self._commitment}

    def _get_token_accounts_by_delegate_body(
        self, delegate: PublicKey, opts: types.TokenAccountOpts, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, types.TokenAccountOpts, Commitment]:
        return types.RPCMethod("getTokenAccountsByDelegate"), str(delegate), opts, commitment or self._commitment

    def _get_token_accounts_by_owner_body(
        self, owner: PublicKey, opts: types.TokenAccountOpts, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, types.TokenAccountOpts, Commitment]:
        return types.RPCMethod("getTokenAccountsByOwner"), str(owner), opts, commitment or self._commitment

    def _get_token_accounts_body(
        self,
        method: types.RPCMethod,
        pubkey: str,
        opts: types.TokenAccountOpts,
        commitment: Commitment,
    ) -> Tuple[types.RPCMethod, str, Dict[str, str], Dict[str, Any]]:
        if not opts.mint and not opts.program_id:
            raise ValueError("Please provide one of mint or program_id")

        acc_opts: Dict[str, str] = {}
        if opts.mint:
            acc_opts["mint"] = str(opts.mint)
        if opts.program_id:
            acc_opts["programId"] = str(opts.program_id)

        rpc_opts: Dict[str, Any] = {self._comm_key: commitment or self._commitment, self._encoding_key: opts.encoding}
        if opts.data_slice:
            rpc_opts[self._data_slice_key] = dict(opts.data_slice._asdict())

        return method, pubkey, acc_opts, rpc_opts

    def _get_token_largest_account_body(
        self, pubkey: Union[str, PublicKey], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Commitment]]:
        return types.RPCMethod("getTokenLargestAccounts"), str(pubkey), {self._comm_key: commitment or self._commitment}

    def _get_token_supply_body(
        self, pubkey: Union[str, PublicKey], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Commitment]]:
        return types.RPCMethod("getTokenSupply"), str(pubkey), {self._comm_key: commitment or self._commitment}

    def _get_transaction_count_body(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getTransactionCount"), {self._comm_key: commitment or self._commitment}

    def _get_vote_accounts_body(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getVoteAccounts"), {self._comm_key: commitment or self._commitment}

    def _request_airdrop_body(
        self, pubkey: Union[PublicKey, str], lamports: int, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, int, Dict[str, Commitment]]:
        return (
            types.RPCMethod("requestAirdrop"),
            str(pubkey),
            lamports,
            {self._comm_key: commitment or self._commitment},
        )

    def _send_raw_transaction_body(
        self, txn: Union[bytes, str], opts: types.TxOpts
    ) -> Tuple[types.RPCMethod, str, Dict[str, Union[bool, Commitment, str, int]]]:

        if isinstance(txn, bytes):
            txn = b64encode(txn).decode("utf-8")
        params: Dict[str, Union[bool, Commitment, str, int]] = {
            self._skip_preflight_key: opts.skip_preflight,
            self._preflight_comm_key: opts.preflight_commitment,
            self._encoding_key: "base64",
        }
        if opts.max_retries is not None:
            params[self._max_retries] = opts.max_retries
        return (
            types.RPCMethod("sendTransaction"),
            txn,
            params,
        )

    @staticmethod
    def _send_raw_transaction_post_send_body(
        resp: types.RPCResponse, opts: types.TxOpts
    ) -> Tuple[types.RPCResponse, Commitment, Optional[int]]:
        return resp, opts.preflight_commitment, opts.last_valid_block_height

    def _simulate_transaction_body(
        self, txn: Union[bytes, str, Transaction], sig_verify: bool, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Union[Commitment, bool, str]]]:
        if isinstance(txn, Transaction):
            if txn.recent_blockhash is None:
                raise ValueError("transaction must have a valid blockhash")
            wire_format = b64encode(txn.serialize()).decode("utf-8")
        elif isinstance(txn, bytes):
            wire_format = txn.decode("utf-8")
        else:
            wire_format = txn

        return (
            types.RPCMethod("simulateTransaction"),
            wire_format,
            {self._comm_key: commitment or self._commitment, "sigVerify": sig_verify, self._encoding_key: "base64"},
        )

    @staticmethod
    def _set_log_filter_body(log_filter: str) -> Tuple[types.RPCMethod, str]:
        return types.RPCMethod("setLogFilter"), log_filter

    @staticmethod
    def _post_send(resp: types.RPCResponse) -> types.RPCResponse:
        error = resp.get("error")
        if error:
            raise RPCException(error)
        if not resp.get("result"):
            raise RPCNoResultException("Failed to send transaction")
        return resp

    @staticmethod
    def parse_recent_blockhash(blockhash_resp: types.RPCResponse) -> Blockhash:
        """Extract blockhash from JSON RPC result."""
        if not blockhash_resp.get("result"):
            raise RuntimeError("failed to get recent blockhash")
        return Blockhash(blockhash_resp["result"]["value"]["blockhash"])

    def _process_blockhash_resp(self, blockhash_resp: types.RPCResponse, used_immediately: bool) -> Blockhash:
        recent_blockhash = self.parse_recent_blockhash(blockhash_resp)
        if self.blockhash_cache:
            slot = blockhash_resp["result"]["context"]["slot"]
            self.blockhash_cache.set(recent_blockhash, slot, used_immediately=used_immediately)
        return recent_blockhash
