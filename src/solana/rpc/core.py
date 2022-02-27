# pylint: disable=too-many-arguments
"""Helper code for api.py and async_api.py."""
from base64 import b64encode
from typing import Any, Dict, List, Optional, Tuple, Union, cast

try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal  # type: ignore

from warnings import warn

from based58 import b58decode, b58encode

from solana.blockhash import Blockhash, BlockhashCache
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc import types
from solana.transaction import Transaction

from .commitment import Commitment, Finalized


class RPCException(Exception):
    """Raised when RPC method returns an error result."""


class RPCNoResultException(Exception):
    """Raised when an RPC method returns no result."""


class UnconfirmedTxError(Exception):
    """Raise when confirming a transaction times out."""


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
    _get_cluster_nodes = types.RPCMethod("getClusterNodes")
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

    def _get_balance_args(
        self, pubkey: Union[PublicKey, str], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Commitment]]:
        return types.RPCMethod("getBalance"), str(pubkey), {self._comm_key: commitment or self._commitment}

    def _get_account_info_args(
        self,
        pubkey: Union[PublicKey, str],
        commitment: Optional[Commitment],
        encoding: str,
        data_slice: Optional[types.DataSliceOpts],
    ) -> Tuple[types.RPCMethod, str, Dict[str, Any]]:
        opts: Dict[str, Any] = {self._encoding_key: encoding, self._comm_key: commitment or self._commitment}
        if data_slice:
            opts[self._data_slice_key] = dict(data_slice._asdict())
        return types.RPCMethod("getAccountInfo"), str(pubkey), opts

    @staticmethod
    def _get_block_commitment_args(slot: int) -> Tuple[types.RPCMethod, int]:
        return types.RPCMethod("getBlockCommitment"), slot

    @staticmethod
    def _get_block_time_args(slot: int) -> Tuple[types.RPCMethod, int]:
        return types.RPCMethod("getBlockTime"), slot

    @staticmethod
    def _get_confirmed_block_args(slot: int, encoding: str) -> Tuple[types.RPCMethod, int, str]:
        return types.RPCMethod("getConfirmedBlock"), slot, encoding

    @staticmethod
    def _get_block_args(slot: int, encoding: str) -> Tuple[types.RPCMethod, int, str]:
        return types.RPCMethod("getBlock"), slot, encoding

    def _get_block_height_args(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getBlockHeight"), {self._comm_key: commitment or self._commitment}

    @staticmethod
    def _get_confirmed_blocks_args(start_slot: int, end_slot: Optional[int]) -> Tuple:
        if end_slot:
            return types.RPCMethod("getConfirmedBlocks"), start_slot, end_slot
        return types.RPCMethod("getConfirmedBlocks"), start_slot

    @staticmethod
    def _get_blocks_args(start_slot: int, end_slot: Optional[int]) -> Tuple:
        if end_slot:
            return types.RPCMethod("getBlocks"), start_slot, end_slot
        return types.RPCMethod("getBlocks"), start_slot

    def _get_confirmed_signature_for_address2_args(
        self,
        account: Union[str, Keypair, PublicKey],
        before: Optional[str],
        until: Optional[str],
        limit: Optional[int],
        commitment: Optional[Commitment],
    ) -> Tuple[types.RPCMethod, str, Dict[str, Union[int, str, Commitment]]]:
        warn(
            "solana.rpc.api.getConfirmedSignaturesForAddress2 is deprecated, "
            "please use solana.rpc.api.getSignaturesForAddress",
            category=DeprecationWarning,
        )
        opts = self._get_signature_for_address_config_arg(before, until, limit, commitment)
        account = self._get_signature_for_address_account_arg(account)
        return types.RPCMethod("getConfirmedSignaturesForAddress2"), account, opts

    def _get_signatures_for_address_args(
        self,
        account: Union[str, Keypair, PublicKey],
        before: Optional[str],
        until: Optional[str],
        limit: Optional[int],
        commitment: Optional[Commitment],
    ) -> Tuple[types.RPCMethod, str, Dict[str, Union[int, str, Commitment]]]:
        opts = self._get_signature_for_address_config_arg(before, until, limit, commitment)
        account = self._get_signature_for_address_account_arg(account)
        return types.RPCMethod("getSignaturesForAddress"), account, opts

    @staticmethod
    def _get_signature_for_address_account_arg(account: Union[str, Keypair, PublicKey]) -> str:
        if isinstance(account, Keypair):
            account = str(account.public_key)
        if isinstance(account, PublicKey):
            account = str(account)
        return account

    def _get_signature_for_address_config_arg(
        self,
        before: Optional[str],
        until: Optional[str],
        limit: Optional[int],
        commitment: Optional[Commitment],
    ) -> Dict[str, Union[int, str, Commitment]]:
        opts: Dict[str, Union[int, str, Commitment]] = {}
        if before:
            opts[self._before_rpc_config_key] = before
        if until:
            opts[self._until_rpc_config_key] = until
        if limit:
            opts[self._limit_rpc_config_key] = limit
        if commitment:
            opts[self._comm_key] = commitment
        return opts

    @staticmethod
    def _get_confirmed_transaction_args(tx_sig: str, encoding: str = "json") -> Tuple[types.RPCMethod, str, str]:
        return types.RPCMethod("getConfirmedTransaction"), tx_sig, encoding

    def _get_transaction_args(
        self, tx_sig: str, encoding: str = "json", commitment: Commitment = None
    ) -> Tuple[types.RPCMethod, str, Dict[str, Union[str, Commitment]]]:

        return (
            types.RPCMethod("getTransaction"),
            tx_sig,
            {self._encoding_key: encoding, self._comm_key: commitment or self._commitment},
        )

    def _get_epoch_info_args(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getEpochInfo"), {self._comm_key: commitment or self._commitment}

    def _get_fee_calculator_for_blockhash_args(
        self, blockhash: Union[str, Blockhash], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Union[str, Blockhash], Dict[str, Commitment]]:
        return (
            types.RPCMethod("getFeeCalculatorForBlockhash"),
            blockhash,
            {self._comm_key: commitment or self._commitment},
        )

    def _get_fees_args(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getFees"), {self._comm_key: commitment or self._commitment}

    def _get_inflation_governor_args(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getInflationGovernor"), {self._comm_key: commitment or self._commitment}

    def _get_largest_accounts_args(
        self, filter_opt: Optional[str], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[Optional[str], Optional[str]]]:
        opt: Dict[Optional[str], Optional[str]] = {"filter": filter_opt} if filter_opt else {}
        opt[self._comm_key] = str(commitment)
        return types.RPCMethod("getLargestAccounts"), opt

    def _get_leader_schedule_args(
        self, epoch: Optional[int], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Optional[int], Dict[str, Commitment]]:
        return types.RPCMethod("getLeaderSchedule"), epoch, {self._comm_key: commitment or self._commitment}

    def _get_minimum_balance_for_rent_exemption_args(
        self, usize: int, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, int, Dict[str, Commitment]]:
        return (
            types.RPCMethod("getMinimumBalanceForRentExemption"),
            usize,
            {self._comm_key: commitment or self._commitment},
        )

    def _get_multiple_accounts_args(
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

    def _get_program_accounts_args(
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

    def _get_recent_blockhash_args(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getRecentBlockhash"), {self._comm_key: commitment or self._commitment}

    @staticmethod
    def _get_signature_statuses_args(
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

    def _get_slot_args(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getSlot"), {self._comm_key: commitment or self._commitment}

    def _get_slot_leader_args(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getSlotLeader"), {self._comm_key: commitment or self._commitment}

    def _get_stake_activation_args(
        self,
        pubkey: Union[PublicKey, str],
        epoch: Optional[int],
        commitment: Optional[Commitment],
    ) -> Tuple[types.RPCMethod, str, Dict[str, Union[int, Commitment]]]:
        opts: Dict[str, Union[int, Commitment]] = {self._comm_key: commitment or self._commitment}
        if epoch:
            opts["epoch"] = epoch

        return types.RPCMethod("getStakeActivation"), str(pubkey), opts

    def _get_supply_args(self, commitment: Optional[Commitment]) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getSupply"), {self._comm_key: commitment or self._commitment}

    def _get_token_account_balance_args(
        self, pubkey: Union[str, PublicKey], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Commitment]]:
        return types.RPCMethod("getTokenAccountBalance"), str(pubkey), {self._comm_key: commitment or self._commitment}

    def _get_token_accounts_by_delegate_args(
        self, delegate: PublicKey, opts: types.TokenAccountOpts, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, types.TokenAccountOpts, Commitment]:
        return types.RPCMethod("getTokenAccountsByDelegate"), str(delegate), opts, commitment or self._commitment

    def _get_token_accounts_by_owner_args(
        self, owner: PublicKey, opts: types.TokenAccountOpts, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, types.TokenAccountOpts, Commitment]:
        return types.RPCMethod("getTokenAccountsByOwner"), str(owner), opts, commitment or self._commitment

    def _get_token_accounts_args(
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

    def _get_token_largest_account_args(
        self, pubkey: Union[str, PublicKey], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Commitment]]:
        return types.RPCMethod("getTokenLargestAccounts"), str(pubkey), {self._comm_key: commitment or self._commitment}

    def _get_token_supply_args(
        self, pubkey: Union[str, PublicKey], commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, Dict[str, Commitment]]:
        return types.RPCMethod("getTokenSupply"), str(pubkey), {self._comm_key: commitment or self._commitment}

    def _get_transaction_count_args(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getTransactionCount"), {self._comm_key: commitment or self._commitment}

    def _get_vote_accounts_args(
        self, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, Dict[str, Commitment]]:
        return types.RPCMethod("getVoteAccounts"), {self._comm_key: commitment or self._commitment}

    def _request_airdrop_args(
        self, pubkey: Union[PublicKey, str], lamports: int, commitment: Optional[Commitment]
    ) -> Tuple[types.RPCMethod, str, int, Dict[str, Commitment]]:
        return (
            types.RPCMethod("requestAirdrop"),
            str(pubkey),
            lamports,
            {self._comm_key: commitment or self._commitment},
        )

    def _send_raw_transaction_args(
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
    def _send_raw_transaction_post_send_args(
        resp: types.RPCResponse, opts: types.TxOpts
    ) -> Tuple[types.RPCResponse, Commitment]:
        return resp, opts.preflight_commitment

    def _simulate_transaction_args(
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
    def _set_log_filter_args(log_filter: str) -> Tuple[types.RPCMethod, str]:
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
