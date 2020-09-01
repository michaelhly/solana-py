"""API client to interact with the Solana JSON RPC Endpoint."""
from __future__ import annotations

from typing import Any, Dict, List, NamedTuple, Optional, Union

from base58 import b58decode, b58encode

from solana.account import Account
from solana.blockhash import Blockhash
from solana.publickey import PublicKey
from solana.transaction import Transaction

from .commitment import Commitment, Max
from .providers import http
from .types import RPCMethod, RPCResponse


class DataSlice(NamedTuple):
    """Data class for "data_slice" parameter.

    Params to limit the returned account data, only available for "base58" or "base64" encoding.
    """

    offset: int
    """Limit the returned account data using the provided offset: <usize>."""
    length: int
    """Limit the returned account data using the provided length: <usize>."""


class Client:  # pylint: disable=too-many-public-methods
    """Client class."""

    _comm_key = "commitment"
    _encoding_key = "encoding"
    _data_slice_key = "dataSlice"

    def __init__(self, endpoint: Optional[str] = None):
        """Init API client."""
        self._provider = http.HTTPProvider(endpoint)

    def is_connected(self) -> bool:
        """Health check.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.is_connected() # doctest: +SKIP
        True
        """
        return self._provider.is_connected()

    def get_balance(self, pubkey: Union[PublicKey, str], commitment: Commitment = Max) -> RPCResponse:
        """Returns the balance of the account of provided Pubkey.

        :param pubkey: Pubkey of account to query, as base-58 encoded string or PublicKey object.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> from solana.publickey import PublicKey
        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_balance(PublicKey(1)) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': {'context': {'slot': 228}, 'value': 0}, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("getBalance"), str(pubkey), {self._comm_key: commitment})

    def get_account_info(
        self,
        pubkey: Union[PublicKey, str],
        commitment: Commitment = Max,
        encoding: str = "base64",
        data_slice: Optional[DataSlice] = None,
    ) -> RPCResponse:
        """Returns all the account info for the specified public key.

        :param pubkey: Pubkey of account to query, as base-58 encoded string or PublicKey object.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".
        :param encoding: (optional) encoding for Account data, either "base58" (slow), "base64", or
            "jsonParsed". Default is "base64".

            - "base58" is limited to Account data of less than 128 bytes.
            - "base64" will return base64 encoded data for Account data of any size.
            - "jsonPrased" encoding attempts to use program-specific state parsers to return more human-readable and explicit account state data.

            If jsonParsed is requested but a parser cannot be found, the field falls back to base64 encoding,
            detectable when the data field is type. (jsonParsed encoding is UNSTABLE).
        :param data_slice: (optional) limit the returned account data using the provided `offset`: <usize> and
            `length`: <usize> fields; only available for "base58" or "base64" encoding.

        >>> from solana.publickey import PublicKey
        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_account_info(PublicKey(1)) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 33265073},
          'value': {'data': '',
           'executable': False,
           'lamports': 4459816188034584,
           'owner': '11111111111111111111111111111111',
           'rentEpoch': 90}},
         'id': 1}
        """  # noqa: E501 # pylint: disable=line-too-long
        opts: Dict[str, Any] = {self._encoding_key: encoding, self._comm_key: commitment}
        if data_slice:
            opts[self._data_slice_key] = dict(data_slice._asdict())
        return self._provider.make_request(RPCMethod("getAccountInfo"), str(pubkey), opts)

    def get_block_commitment(self, slot: int) -> RPCResponse:
        """Fetch the commitment for particular block.

        :param slot: Block, identified by Slot.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_block_commitment(0) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'commitment': [0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           0,
           497717120],
          'totalStake': 497717120},
          'id': 1}}
        """
        return self._provider.make_request(RPCMethod("getBlockCommitment"), slot)

    def get_block_time(self, slot: int) -> RPCResponse:
        """Fetch the estimated production time of a block.

        :param slot: Block, identified by Slot

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_block_time(5) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1598400007, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("getBlockTime"), slot)

    def get_cluster_nodes(self) -> RPCResponse:
        """Returns information about all the nodes participating in the cluster.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_cluster_nodes() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': [{'gossip': '127.0.0.1:8001',
           'pubkey': 'LjvEBM78ufAikBfxqtj4RNiAECUi7Xqtz9k3QM3DzPk',
           'rpc': '127.0.0.1:8899',
           'tpu': '127.0.0.1:8003',
           'version': '1.4.0 5332fcad'}],
         'id': 1}
        """
        return self._provider.make_request(RPCMethod("getClusterNodes"))

    def get_confirmed_block(
        self,
        slot: int,
        encoding: str = "json",
    ) -> RPCResponse:
        """Returns identity and transaction information about a confirmed block in the ledger.

        :param slot: start_slot, as u64 integer.
        :param encoding: (optional) encoding for the returned Transaction, either "json", "jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_confirmed_block(1) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'blockTime': None,
          'blockhash': '39pJzWsPn59k2PuHqhB7xNYBNGFXcFVkXLertHPBV4Tj',
          'parentSlot': 0,
          'previousBlockhash': 'EwF9gtehrrvPUoNticgmiEadAWzn4XeN8bNaNVBkS6S2',
          'rewards': [],
          'transactions': [{'meta': {'err': None,
             'fee': 0,
             'postBalances': [500000000000, 26858640, 1, 1, 1],
             'preBalances': [500000000000, 26858640, 1, 1, 1],
             'status': {'Ok': None}},
            'transaction': {'message': {'accountKeys': ['LjvEBM78ufAikBfxqtj4RNiAECUi7Xqtz9k3QM3DzPk',
               'EKAar3bMQUZvGSonq7vcPF2nPaCYowbnat44FPafW8Po',
               'SysvarS1otHashes111111111111111111111111111',
               'SysvarC1ock11111111111111111111111111111111',
               'Vote111111111111111111111111111111111111111'],
              'header': {'numReadonlySignedAccounts': 0,
               'numReadonlyUnsignedAccounts': 3,
               'numRequiredSignatures': 1},
              'instructions': [{'accounts': [1, 2, 3, 0],
                'data': '37u9WtQpcm6ULa3VmTgTKEBCtYMxq84mk82tRvKdFEwj3rALiptAzuMJ1yoVSFAMARMZYp7q',
                'programIdIndex': 4}],
              'recentBlockhash': 'EwF9gtehrrvPUoNticgmiEadAWzn4XeN8bNaNVBkS6S2'},
             'signatures': ['63jnpMCs7TNnCjnTqUrX7Mvqc5CbJMtVkLxBjPHUQkjXyZrQuZpfhjvzA7A29D9tMqVaiQC3UNP1NeaZKFFHJyQE']}}]},
         'id': 9}
        >>> solana_client.get_confirmed_block(1, encoding="base64") # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'blockTime': None,
          'blockhash': '39pJzWsPn59k2PuHqhB7xNYBNGFXcFVkXLertHPBV4Tj',
          'parentSlot': 0,
          'previousBlockhash': 'EwF9gtehrrvPUoNticgmiEadAWzn4XeN8bNaNVBkS6S2',
          'rewards': [],
          'transactions': [{'meta': {'err': None,
             'fee': 0,
             'postBalances': [500000000000, 26858640, 1, 1, 1],
             'preBalances': [500000000000, 26858640, 1, 1, 1],
             'status': {'Ok': None}},
            'transaction': ['AfxyKHmHIjXWjkyHODGeAbVxmfQWPj1ydS9nF+ynJHo8I1vCPDp2P9Cj5aA6W1CAHEHCqY0B1FDKomCzRo3qrAsBAAMFBQ6QBWfhQF7rG02xhuEsmmrUtz3AUjBtJKkqaHPJEmvFzziDX0C0robPrl9RbOyXHoc9/Dxa0zoGL6cEjvCjLgan1RcZLwqvxvJl4/t3zHragsUp0L47E24tAFUgAAAABqfVFxjHdMkoVmOYaR1etoteuKObS21cc1VbIQAAAAAHYUgdNXR0u3xNdiTr072z2DVec9EQQ/wNo1OAAAAAAM8NSv7ISDPN9E9XNL9vX7h8LuJHWlopUcX39DxsDx23AQQEAQIDADUCAAAAAQAAAAAAAAAAAAAAAAAAAIWWp5Il3Kg312pzVk6Jt61iyFhTbtmkh/ORbj3JUQRbAA==',
             'base64']}]},
         'id': 10}
        """  # noqa: E501 # pylint: disable=line-too-long
        return self._provider.make_request(RPCMethod("getConfirmedBlock"), slot, encoding)

    def get_confirmed_blocks(self, start_slot: int, end_slot: Optional[int] = None) -> RPCResponse:
        """Returns a list of confirmed blocks.

        :param start_slot: start_slot, as u64 integer.
        :param end_slot: (optional) encoding for the returned Transaction, either "json", "jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_confirmed_blocks(5, 10) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': [5, 6, 7, 8, 9, 10], 'id': 1}
        """
        if end_slot:
            return self._provider.make_request(RPCMethod("getConfirmedBlocks"), start_slot, end_slot)
        return self._provider.make_request(RPCMethod("getConfirmedBlocks"), start_slot)

    def get_confirmed_signature_for_address2(
        self, account: Union[str, Account, PublicKey], before: Optional[str] = None, limit: Optional[int] = None
    ) -> RPCResponse:
        """Returns confirmed signatures for transactions involving an address.

        Signatures are returned backwards in time from the provided signature or
        most recent confirmed block.

        :param account: Account to be queried
        :param before: (optional) start searching backwards from this transaction signature
            If not provided the search starts from the top of the highest max confirmed block
        :param limit: (optoinal) maximum transaction signatures to return (between 1 and 1,000, default: 1,000)

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_confirmed_signature_for_address2("Vote111111111111111111111111111111111111111", limit=1) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': [{'err': None,
           'memo': None,
           'signature': 'v1BK8XcaPBzAGd7TB1K53pMdi6TBGe5CLCgx8cmZ4Bj63ZNvA6ca2QaxFpBFdvmpoFQ51VorBjifkBGLTDhwpqN',
           'slot': 4290}],
         'id': 2}
        """  # noqa: E501 # pylint: disable=line-too-long
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
            instruction parsers to return more human-readable and explicit data in the
            `transaction.message.instructions` list
        :param encoding: (optional) encoding for the returned Transaction, either "json", "jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_confirmed_transaction("3PtGYH77LhhQqTXP4SmDVJ85hmDieWsgXCUbn14v7gYyVYPjZzygUQhTk3bSTYnfA48vCM1rmWY7zWL3j1EVKmEy") # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'meta': {'err': None,
           'fee': 5000,
           'postBalances': [498449233720610510, 1000001001987940, 1],
           'preBalances': [498449233721615510, 1000001000987940, 1],
           'status': {'Ok': None}},
          'slot': 1659335,
          'transaction': {'message': {'accountKeys': ['9B5XszUGdMaxCZ7uSQhPzdks5ZQSmWxrmzCSvtJ6Ns6g',
             '2KW2XRd9kwqet15Aha2oK3tYvd3nWbTFH1MBiRAv1BE1',
             '11111111111111111111111111111111'],
            'header': {'numReadonlySignedAccounts': 0,
             'numReadonlyUnsignedAccounts': 1,
             'numRequiredSignatures': 1},
            'instructions': [{'accounts': [0, 1],
              'data': '3Bxs4Bc3VYuGVB19',
              'programIdIndex': 2}],
            'recentBlockhash': 'FwcsKNptGtMLccXAA9YgnivVFK95mKzECLT1DNPi3SDr'},
           'signatures': ['3PtGYH77LhhQqTXP4SmDVJ85hmDieWsgXCUbn14v7gYyVYPjZzygUQhTk3bSTYnfA48vCM1rmWY7zWL3j1EVKmEy']}},
         'id': 4}
        """  # noqa: E501 # pylint: disable=line-too-long
        return self._provider.make_request(RPCMethod("getConfirmedTransaction"), tx_sig, encoding)

    def get_epoch_info(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns information about the current epoch.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_epoch_info() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'absoluteSlot': 5150,
          'blockHeight': 5150,
          'epoch': 0,
          'slotIndex': 5150,
          'slotsInEpoch': 8192},
         'id': 5}
        """
        return self._provider.make_request(RPCMethod("getEpochInfo"), {self._comm_key: commitment})

    def get_epoch_schedule(self) -> RPCResponse:
        """Returns epoch schedule information from this cluster's genesis config.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_epoch_schedule() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'firstNormalEpoch': 0,
          'firstNormalSlot': 0,
          'leaderScheduleSlotOffset': 8192,
          'slotsPerEpoch': 8192,
          'warmup': False},
         'id': 6}
        """
        return self._provider.make_request(RPCMethod("getEpochSchedule"))

    def get_fee_calculator_for_blockhash(
        self, blockhash: Union[str, Blockhash], commitment: Commitment = Max
    ) -> RPCResponse:
        """Returns the fee calculator associated with the query blockhash, or null if the blockhash has expired.

        :param blockhash: Blockhash to query as a Base58 encoded string.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_fee_calculator_for_blockhash("BaQSR194dC4dZaRxATtxYyEwDkk7VgqUY8NVNkub8HFZ") # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 7065},
          'value': {'feeCalculator': {'lamportsPerSignature': 5000}}},
         'id': 4}
        """  # noqa: E501 # pylint: disable=line-too-long
        return self._provider.make_request(
            RPCMethod("getFeeCalculatorForBlockhash"), blockhash, {self._comm_key: commitment}
        )

    def get_fee_rate_governor(self) -> RPCResponse:
        """Returns the fee rate governor information from the root bank.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_fee_rate_governor() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 7172},
          'value': {'feeRateGovernor': {'burnPercent': 50,
            'maxLamportsPerSignature': 100000,
            'minLamportsPerSignature': 5000,
            'targetLamportsPerSignature': 10000,
            'targetSignaturesPerSlot': 20000}}},
         'id': 5}
        """
        return self._provider.make_request(RPCMethod("getFeeRateGovernor"))

    def get_fees(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns a recent block hash from the ledger, a fee schedule and the last slot the blockhash will be valid.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_fees() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 7727},
          'value': {'blockhash': 'GGS6AEDqjF5irU6D6VQNherEZ2hckGaeBiVdfSZKg4gd',
           'feeCalculator': {'lamportsPerSignature': 5000},
           'lastValidSlot': 8027}},
         'id': 1}
        """
        return self._provider.make_request(RPCMethod("getFees"), {self._comm_key: commitment})

    def get_first_available_block(self) -> RPCResponse:
        """Returns the slot of the lowest confirmed block that has not been purged from the ledger.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_fees() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1, 'id': 2}
        """
        return self._provider.make_request(RPCMethod("getFirstAvailableBlock"))

    def get_genesis_hash(self) -> RPCResponse:
        """Returns the genesis hash.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_genesis_hash() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'EwF9gtehrrvPUoNticgmiEadAWzn4XeN8bNaNVBkS6S2',
         'id': 3}
        """
        return self._provider.make_request(RPCMethod("getGenesisHash"))

    def get_identity(self) -> RPCResponse:
        """Returns the identity pubkey for the current node.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_identity() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'identity': 'LjvEBM78ufAikBfxqtj4RNiAECUi7Xqtz9k3QM3DzPk'},
         'id': 4}
        """
        return self._provider.make_request(RPCMethod("getIdentity"))

    def get_inflation_governor(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns the current inflation governor.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_inflation_governor() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'foundation': 0.05,
          'foundationTerm': 7.0,
          'initial': 0.15,
          'taper': 0.15,
          'terminal': 0.015},
         'id': 5}
        """
        return self._provider.make_request(RPCMethod("getInflationGovernor"), {self._comm_key: commitment})

    def get_inflation_rate(self) -> RPCResponse:
        """Returns the specific inflation values for the current epoch.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_inflation_governor() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'epoch': 1,
          'foundation': 0.007499746885736559,
          'total': 0.14999493771473116,
          'validator': 0.1424951908289946},
         'id': 1}
        """
        return self._provider.make_request(RPCMethod("getInflationRate"))

    def get_largest_accounts(self, filter_opt: Optional[str] = None, commitment: Commitment = Max) -> RPCResponse:
        """Returns the 20 largest accounts, by lamport balance.

        :param opt: Filter results by account type; currently supported: circulating|nonCirculating.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_largest_accounts() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 8890},
          'value': [{'address': '95L7AsBCLRsqghsi6ksZkzjNbs6rqDgHCzKaGZ7bJi75',
            'lamports': 500000000000000000},
           {'address': 'APnSR52EC1eH676m7qTBHUJ1nrGpHYpV7XKPxgRDD8gX',
            'lamports': 164511033098290000},
           {'address': '13LeFbG6m2EP1fqCj9k66fcXsoTHMMtgr7c78AivUrYD',
            'lamports': 153333632446109120},
           {'address': 'GK2zqSsXLA2rwVZk347RYhh6jJpRsCA69FjLW93ZGi3B',
            'lamports': 57499999036109120},
           {'address': '8HVqyX9jebh31Q9Hp8t5sMVJs665979ZeEr3eCfzitUe',
            'lamports': 30301031036109120},
           {'address': 'HbZ5FfmKWNHC7uwk6TF1hVi6TCs7dtYfdjEcuPGgzFAg',
            'lamports': 14999999036109120},
           {'address': '14FUT96s9swbmH7ZjpDvfEDywnAYy9zaNhv4xvezySGu',
            'lamports': 4999999036109120},
           {'address': '9huDUZfxoJ7wGMTffUE7vh1xePqef7gyrLJu9NApncqA',
            'lamports': 4999999036109120},
           {'address': 'C7C8odR8oashR5Feyrq2tJKaXL18id1dSj2zbkDGL2C2',
            'lamports': 4999999036109120},
           {'address': 'AYgECURrvuX6GtFe4tX7aAj87Xc5r5Znx96ntNk1nCv',
            'lamports': 2499999518054560},
           {'address': 'AogcwQ1ubM76EPMhSD5cw1ES4W5econvQCFmBL6nTW1',
            'lamports': 2499999518054560},
           {'address': 'gWgqQ4udVxE3uNxRHEwvftTHwpEmPHAd8JR9UzaHbR2',
            'lamports': 2499999518054560},
           {'address': '3D91zLQPRLamwJfGR5ZYMKQb4C18gsJNaSdmB6b2wLhw',
            'lamports': 2499999518054560},
           {'address': '3bHbMa5VW3np5AJazuacidrN4xPZgwhcXigmjwHmBg5e',
            'lamports': 2499999518054560},
           {'address': '4U3RFq7X5kLG6tZ9kcksFL8oXeGNjtuUN1YfkVKXbs5x',
            'lamports': 2499999518054560},
           {'address': '5cBVGBKY6kBaiTVmsQpxThJ2oqitBYuCAX9Zm2zMuV4y',
            'lamports': 2499999518054560},
           {'address': '8PjJTv657aeN9p5R2WoM6pPSz385chvTTytUWaEjSjkq',
            'lamports': 2499999518054560},
           {'address': 'AHB94zKUASftTdqgdfiDSdnPJHkEFp7zX3yMrcSxABsv',
            'lamports': 2499999518054560},
           {'address': 'Hc36Wh1ZqYGzGAnsJWNT9r2gY3h9n89uDpxZPsmEsiE3',
            'lamports': 2499999518054560},
           {'address': 'GxyRKP2eVKACaSSnso4VLSAjZKmHsFXHWUfS3A5CtiMA',
            'lamports': 1940147018054560}]},
         'id': 2}
        """
        opt: Dict[Optional[str], Optional[str]] = {"filter": filter_opt} if filter_opt else {}
        opt[self._comm_key] = str(commitment)
        return self._provider.make_request(RPCMethod("getLargestAccounts"), opt)

    def get_leader_schedule(self, epoch: Optional[int] = None, commitment: Commitment = Max) -> RPCResponse:
        """Returns the leader schedule for an epoch.

        :param epoch: Fetch the leader schedule for the epoch that corresponds to the provided slot.
            If unspecified, the leader schedule for the current epoch is fetched.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_leader_schedule() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'EWj2cuEuVhi7RX81cnAY3TzpyFwnHzzVwvuTyfmxmhs3': [0,
           1,
           2,
           3,
           4,
           5,
           ...]},
         'id': 6}
        """
        return self._provider.make_request(RPCMethod("getLeaderSchedule"), epoch, {self._comm_key: commitment})

    def get_minimum_balance_for_rent_exemption(self, usize: int, commitment: Commitment = Max) -> RPCResponse:
        """Returns minimum balance required to make account rent exempt.

        :param usize: Account data length.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_minimum_balance_for_rent_exemption(50) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1238880, 'id': 7}
        """
        return self._provider.make_request(
            RPCMethod("getMinimumBalanceForRentExemption"), usize, {self._comm_key: commitment}
        )

    def get_program_accounts(  # pylint: disable=too-many-arguments
        self,
        pubkey: Union[str, PublicKey],
        data_size: Optional[int] = None,
        encoding: Optional[str] = None,
        filter_opts: Optional[Dict] = None,
        commitment: Commitment = Max,
        data_slice: Optional[DataSlice] = None,
    ) -> RPCResponse:
        """Returns all accounts owned by the provided program Pubkey.

        :param pubkey: Pubkey of program, as base-58 encoded string or PublicKey object
        :param encoding: (optional) encoding for the returned Transaction, either jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.
        :param data_slice: (optional) limit the returned account data using the provided `offset`: <usize> and
            `length`: <usize> fields; only available for "base58" or "base64" encoding.
        :param filter_opts: (optional) filter results using various
            `filter objects <https://docs.solana.com/apps/jsonrpc-api#filters/>`_;
            account must meet all filter criteria to be included in results.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> filter_opts = {"memcmp": {"offset": 4, "bytes": "3Mc6vR"}}
        >>> solana_client.get_program_accounts("4Nd1mBQtrMJVYVfKf2PJy9NZUZdTAsp7D4xWLs4gDB4T", data_size=17, filter_opts=filter_opts) # doctest: +SKIP
        {'jsonrpc': "2.0",
         'result' :[{
            'account' :{
                 'data' :'2R9jLfiAQ9bgdcw6h8s44439',
                 'executable' :false,
                 'lamports' :15298080,
                 'owner' :'4Nd1mBQtrMJVYVfKf2PJy9NZUZdTAsp7D4xWLs4gDB4T',
                 'rentEpoch' :28},
            'pubkey' :'CxELquR1gPP8wHe33gZ4QxqGB3sZ9RSwsJ2KshVewkFY'}],
         'id' :1}
        """  # noqa: E501 # pylint: disable=line-too-long
        opts: Dict[str, Any] = {"filters": []}
        if data_size:
            opts["filters"].append({"dataSize": data_size})
        if filter_opts:
            opts["filters"].append(filter_opts)
        if encoding:
            opts[self._encoding_key] = encoding
        if data_slice:
            opts[self._data_slice_key] = dict(data_slice._asdict())
        opts[self._comm_key] = commitment

        return self._provider.make_request(RPCMethod("getProgramAccounts"), str(pubkey), opts)

    def get_recent_blockhash(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns a recent block hash from the ledger.

        Response also includes a fee schedule that can be used to compute the cost
        of submitting a transaction using it.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_recent_blockhash() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 1637},
          'value': {'blockhash': 'EALChog1mXQ9nEgEUQpWAtmA5UueUZvZiL16ZivmR7eb',
           'feeCalculator': {'lamportsPerSignature': 5000}}},
         'id': 2}
        """
        return self._provider.make_request(RPCMethod("getRecentBlockhash"), {self._comm_key: commitment})

    def get_signature_statuses(
        self, signatures: List[Union[str, bytes]], search_transaction_history: bool = False
    ) -> RPCResponse:
        """Returns the statuses of a list of signatures.

        Unless the `searchTransactionHistory` configuration parameter is included, this method only
        searches the recent status cache of signatures, which retains statuses for all active slots plus
        `MAX_RECENT_BLOCKHASHES` rooted slots.

        :param signatures: An array of transaction signatures to confirm.
        :param search_transaction_history: If true, a Solana node will search its ledger cache for
            any signatures not found in the recent status cache

        >>> solana_client = Client("http://localhost:8899")
        >>> signatures = [
        ...     "5VERv8NMvzbJMEkV8xnrLkEaWRtSz9CosKDYjCJjBRnbJLgp8uirBgmQpjKhoR4tjF3ZpRzrFmBV6UjKdiSZkQUW",
        ...     "5j7s6NiJS3JAkvgkoc18WVAsiSaci2pxB2A6ueCJP4tprA2TFg9wSyTLeYouxPBJEMzJinENTkpA52YStRW5Dia7"]
        >>> solana_client.get_signature_statuses(signatures) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {
            'context': {'slot':82},
            'value': [{
                'slot': 72,
                'confirmations': 10,
                'err': null,
                'status': {'Ok': null}}, null]},
         'id': 1}
        """
        base58_sigs: List[str] = []
        for sig in signatures:
            if isinstance(sig, str):
                base58_sigs.append(b58encode(b58decode(sig)).decode("utf-8"))
            else:
                base58_sigs.append(b58encode(sig).decode("utf-8"))

        return self._provider.make_request(
            RPCMethod("getSignatureStatuses"), base58_sigs, {"searchTransactionHistory": search_transaction_history}
        )

    def get_slot(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns the current slot the node is processing.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_slot() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 7515, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("getSlot"), {self._comm_key: commitment})

    def get_slot_leader(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns the current slot leader.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_slot_leader() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'EWj2cuEuVhi7RX81cnAY3TzpyFwnHzzVwvuTyfmxmhs3',
         'id': 1}
        """
        return self._provider.make_request(RPCMethod("getSlotLeader"), {self._comm_key: commitment})

    def get_stake_activation(
        self, pubkey: Union[PublicKey, str], epoch: Optional[int] = None, commitment: Commitment = Max
    ):
        """Returns epoch activation information for a stake account.

        :param pubkey: Pubkey of stake account to query, as base-58 encoded string or PublicKey object
        :param epoch: (optional) epoch for which to calculate activation details. If parameter not provided,
            defaults to current epoch
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_stake_activation() # doctest: +SKIP
        {'jsonrpc': '2.0','result': {'active': 124429280, 'inactive': 73287840, 'state': 'activating'}, 'id': 1}}
        """
        opts: Dict[str, Union[int, Commitment]] = {self._comm_key: commitment}
        if epoch:
            opts["epoch"] = epoch

        return self._provider.make_request(RPCMethod("getStakeActivation"), str(pubkey), opts)

    def get_supply(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns information about the current supply.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_supply() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 3846},
          'value': {'circulating': 683635192454157660,
           'nonCirculating': 316364808037127120,
           'nonCirculatingAccounts': ['ETfDYz7Cg5p9SDFmdpRerjBN5puKK7xydEBZZGM2V4Ay',
            '7cKxv6UznFoWRuJkgw5bWj5rp5PiKTcXZeEaLqyd3Bbm',
            'CV7qh8ZoqeUSTQagosGpkLptXoojf9yCszxkRx1jTD12',
            'FZ9S7X9jMbCaMyJjRfSoBhFyarUMVwvx7HWRe4LnZHsg',
             ...]
           'total': 1000000000491284780}},
         'id': 1}
        """
        return self._provider.make_request(RPCMethod("getSupply"), {self._comm_key: commitment})

    def get_token_account_balance(self, pubkey: Union[str, PublicKey], commitment: Commitment = Max):
        """Returns the token balance of an SPL Token account (UNSTABLE).

        :param pubkey: Pubkey of Token account to query, as base-58 encoded string or PublicKey object.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_token_account_balance("7fUAJdStEuGbc3sM84cKRL6yYaaSstyLSU4ve5oovLS7") # doctest: +SKIP
        {'jsonrpc': '2.0','result': {
            'context': {'slot':1114},
            'value': {
                'uiAmount': 98.64,
                'amount': '9864',
                'decimals': 2},
         'id' :1}
        """
        return self._provider.make_request(
            RPCMethod("getTokenAccountBalance"), str(pubkey), {self._comm_key: commitment}
        )

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

    def get_transaction_count(self, commitment: Commitment = Max) -> RPCResponse:
        """Returns the current Transaction count from the ledger.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_transaction_count() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 4554, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("getTransactionCount"), {self._comm_key: commitment})

    def get_minimum_ledger_slot(self) -> RPCResponse:
        """Returns the lowest slot that the node has information about in its ledger.

        This value may increase over time if the node is configured to purge older ledger data.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_minimum_ledger_slot() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1234, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("minimumLedgerSlot"))

    def get_version(self) -> RPCResponse:
        """Returns the current solana versions running on the node.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_version() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': {'solana-core': '1.4.0 5332fcad'}, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("getVersion"))

    def get_vote_accounts(self, commitment: Commitment = Max):
        """Returns the account info and associated stake for all the voting accounts in the current bank.

        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_vote_accounts() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'current': [{'activatedStake': 0,
            'commission': 100,
            'epochCredits': [[165, 714644, 707372],
             [166, 722092, 714644],
             [167, 730285, 722092],
             [168, 738476, 730285],
             ...]
            'epochVoteAccount': True,
            'lastVote': 1872294,
            'nodePubkey': 'J7v9ndmcoBuo9to2MnHegLnBkC9x3SAVbQBJo5MMJrN1',
            'rootSlot': 1872263,
            'votePubkey': 'HiFjzpR7e5Kv2tdU9jtE4FbH1X8Z9Syia3Uadadx18b5'},
           {'activatedStake': 500029968930560,
            'commission': 100,
            'epochCredits': [[165, 1359689, 1351498],
             [166, 1367881, 1359689],
             [167, 1376073, 1367881],
             [168, 1384265, 1376073],
             ...],
            'epochVoteAccount': True,
            'lastVote': 1872295,
            'nodePubkey': 'dv1LfzJvDF7S1fBKpFgKoKXK5yoSosmkAdfbxBo1GqJ',
            'rootSlot': 1872264,
            'votePubkey': '5MMCR4NbTZqjthjLGywmeT66iwE9J9f7kjtxzJjwfUx2'},
           {'activatedStake': 0,
            'commission': 100,
            'epochCredits': [[227, 2751, 0], [228, 7188, 2751]],
            'epochVoteAccount': True,
            'lastVote': 1872295,
            'nodePubkey': 'H1wDvJ5HJc1SzhHoWtaycpzQpFbsL7g8peaRV3obKShs',
            'rootSlot': 1872264,
            'votePubkey': 'DPqpgoLQVU3aq72HEqSMsB9qh4KoXc9fGEpvgEuiwnp6'}],
          'delinquent': []},
         'id': 1}
        """
        return self._provider.make_request(RPCMethod("getVoteAccounts"), {self._comm_key: commitment})

    def request_airdrop(
        self, pubkey: Union[PublicKey, str], lamports: int, commitment: Commitment = Max
    ) -> RPCResponse:
        """Requests an airdrop of lamports to a Pubkey.

        :param pubkey: Pubkey of account to receive lamports, as base-58 encoded string or public key object.
        :param lamports: Amout of lamports.
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> from solana.publickey import PublicKey
        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.request_airdrop(PublicKey(1), 10000) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'uK6gbLbhnTEgjgmwn36D5BRTRkG4AT8r7Q162TLnJzQnHUZVL9r6BYZVfRttrhmkmno6Fp4VQELzL4AiriCo61U',
         'id': 1}
        """
        return self._provider.make_request(
            RPCMethod("requestAirdrop"), str(pubkey), lamports, {self._comm_key: commitment}
        )

    def send_raw_transaction(self, txn: Union[bytes, str, Transaction]) -> RPCResponse:
        """Send a transaction that has already been signed and serialized into the wire format.

        :param txn: Fully-signed Transaction object, a fully sign transaction in wire format,
            or a fully transaction as base-58 encoded string.

        Before submitting, the following preflight checks are performed:

            - The transaction signatures are verified

            - The transaction is simulated against the latest max confirmed bank and on failure an error
                will be returned. Preflight checks may be disabled if desired.

        >>> solana_client = Client("http://localhost:8899")
        >>> full_signed_tx_str = (
        ...     "4hXTCkRzt9WyecNzV1XPgCDfGAZzQKNxLXgynz5QDuWWPSAZBZSHptvWRL3BjCvzUXRdKvHL2b7yGrRQcWyaqsaBCncVG7BFggS8w9snUts67BSh3EqKpXLUm5UMHfD7ZBe9GhARjbNQMLJ1QD3Spr6oMTBU6EhdB4RD8CP2xUxr2u3d6fos36PD98XS6oX8TQjLpsMwncs5DAMiD4nNnR8NBfyghGCWvCVifVwvA8B8TJxE1aiyiv2L429BCWfyzAme5sZW8rDb14NeCQHhZbtNqfXhcp2tAnaAT")
        >>> solana_client.send_raw_transaction(full_signed_tx_str)  # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'CMwyESM2NE74mghfbvsHJDERF7xMYKshwwm6VgH6GFqXzx8LfBFuP5ruccumfhTguha6seUHPpiHzzHUQXzq2kN',
         'id': 1}
        """  # noqa: E501 # pylint: disable=line-too-long
        if isinstance(txn, Transaction):
            wire_format = b58encode(txn.serialize()).decode("utf-8")
        elif isinstance(txn, bytes):
            wire_format = b58encode(txn).decode("utf-8")
        else:
            wire_format = txn

        return self._provider.make_request(RPCMethod("sendTransaction"), wire_format)

    def send_transaction(self, txn: Transaction, *signers: Account) -> RPCResponse:
        """Send a transaction.

        :param txn: Transaction object.
        :param signers: Signers to sign the transaction

        >>> from solana.account import Account
        >>> from solana.system_program import TransferParams, transfer
        >>> sender, reciever = Account(1), Account(2)
        >>> tx = transfer(TransferParams(
        ...     from_pubkey=sender.public_key(), to_pubkey=reciever.public_key(), lamports=1000))
        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.send_transaction(tx, sender) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': '236zSA5w4NaVuLXXHK1mqiBuBxkNBu84X6cfLBh1v6zjPrLfyECz4zdedofBaZFhs4gdwzSmij9VkaSo2tR5LTgG',
         'id': 12}
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

    def simulate_transaction(
        self, txn: Union[bytes, str, Transaction], sig_verify: bool = False, commitment: Commitment = Max
    ) -> RPCResponse:
        """Simulate sending a transaction.

        :param txn: a Transaction object, a transaction in wire format, or a transaction as base-58 encoded string
            The transaction must have a valid blockhash, but is not required to be signed.
        :param signer_verify: if true the transaction signatures will be verified (default: false).
        :param commitment: which bank state to query. It can be either "max", "root", "single" or "recent".

        >>> solana_client = Client("http://localhost:8899")
        >>> tx_str = (
        ...     "4hXTCkRzt9WyecNzV1XPgCDfGAZzQKNxLXgynz5QDuWWPSAZBZSHptvWRL3BjCvzUXRdKvHL2b7yGrRQcWyaqsaBCncVG7BFggS8w9snUts67BSh3EqKpXLUm5UMHfD7ZBe9GhARjbNQMLJ1QD3Spr6oMTBU6EhdB4RD8CP2xUxr2u3d6fos36PD98XS6oX8TQjLpsMwncs5DAMiD4nNnR8NBfyghGCWvCVifVwvA8B8TJxE1aiyiv2L429BCWfyzAme5sZW8rDb14NeCQHhZbtNqfXhcp2tAnaAT")
        >>> solana_client.simulate_transaction(tx_str)  # doctest: +SKIP
        {'jsonrpc' :'2.0',
         'result': {'context': {'slot': 218},
         'value': {
             'err': null,
             'logs': ['BPF program 83astBRguLMdt2h5U1Tpdq5tjFoJ6noeGwaY3mDLVcri success']},
         'id':1}
        """  # noqa: E501 # pylint: disable=line-too-long
        if isinstance(txn, Transaction):
            try:
                b58decode(str(txn.recent_blockhash))
            except Exception as err:
                raise ValueError("transaction must have a valid blockhash") from err

            wire_format = b58encode(txn.serialize()).decode("utf-8")
        elif isinstance(txn, bytes):
            wire_format = b58encode(txn).decode("utf-8")
        else:
            wire_format = txn

        opts = {self._comm_key: commitment, "sigVerify": sig_verify}
        return self._provider.make_request(RPCMethod("simulateTransaction"), wire_format, opts)

    def set_log_filter(self, log_filter: str) -> RPCResponse:
        """Sets the log filter on the validator.

        :param log_filter: The new log filter to use.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.set_log_filter("solana_core=debug") # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': None, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("setLogFilter"), log_filter)

    def validator_exit(self) -> RPCResponse:
        """Request to have the validator exit.

        Validator must have booted with RPC exit enabled (`--enable-rpc-exit` parameter).

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.validator_exit() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': true, 'id': 1}
        """
        return self._provider.make_request(RPCMethod("validatorExit"))
