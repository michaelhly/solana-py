"""API client to interact with the Solana JSON RPC Endpoint."""  # pylint: disable=too-many-lines
from __future__ import annotations

from time import sleep
from typing import List, Optional, Union
from warnings import warn

from solana.account import Account
from solana.blockhash import Blockhash
from solana.publickey import PublicKey
from solana.rpc import types
from solana.transaction import Transaction

from .commitment import Commitment, Finalized
from .core import _ClientCore
from .providers import http


def DataSliceOpt(*args, **kwargs) -> types.DataSliceOpts:  # pylint: disable=invalid-name
    """Option to limit the returned account data, only available for "base58" or "base64" encoding."""
    warn(
        "solana.rpc.api.DataSliceOpt is deprecated, please use solana.rpc.types.DataSliceOpts",
        category=DeprecationWarning,
    )
    return types.DataSliceOpts(*args, **kwargs)


def MemcmpOpt(*args, **kwargs) -> types.MemcmpOpts:  # pylint: disable=invalid-name
    """Option to compare a provided series of bytes with program account data at a particular offset."""
    warn("solana.rpc.api.MemcmpOpt is deprecated, please use solana.rpc.types.MemcmpOpts", category=DeprecationWarning)
    return types.MemcmpOpts(*args, **kwargs)


class Client(_ClientCore):  # pylint: disable=too-many-public-methods
    """Client class."""

    def __init__(self, endpoint: Optional[str] = None, commitment: Optional[Commitment] = None):
        """Init API client."""
        super().__init__(commitment)
        self._provider = http.HTTPProvider(endpoint)

    def is_connected(self) -> bool:
        """Health check.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.is_connected() # doctest: +SKIP
        True
        """
        return self._provider.is_connected()

    def get_balance(self, pubkey: Union[PublicKey, str], commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns the balance of the account of provided Pubkey.

        :param pubkey: Pubkey of account to query, as base-58 encoded string or PublicKey object.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> from solana.publickey import PublicKey
        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_balance(PublicKey(1)) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': {'context': {'slot': 228}, 'value': 0}, 'id': 1}
        """
        args = self._get_balance_args(pubkey, commitment)
        return self._provider.make_request(*args)

    def get_account_info(
        self,
        pubkey: Union[PublicKey, str],
        commitment: Optional[Commitment] = None,
        encoding: str = "base64",
        data_slice: Optional[types.DataSliceOpts] = None,
    ) -> types.RPCResponse:
        """Returns all the account info for the specified public key.

        :param pubkey: Pubkey of account to query, as base-58 encoded string or PublicKey object.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".
        :param encoding: (optional) Encoding for Account data, either "base58" (slow), "base64", or
            "jsonParsed". Default is "base64".

            - "base58" is limited to Account data of less than 128 bytes.
            - "base64" will return base64 encoded data for Account data of any size.
            - "jsonPrased" encoding attempts to use program-specific state parsers to return more human-readable and explicit account state data.

            If jsonParsed is requested but a parser cannot be found, the field falls back to base64 encoding,
            detectable when the data field is type. (jsonParsed encoding is UNSTABLE).
        :param data_slice: (optional) Option to limit the returned account data using the provided `offset`: <usize> and
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
        args = self._get_account_info_args(
            pubkey=pubkey, commitment=commitment, encoding=encoding, data_slice=data_slice
        )
        return self._provider.make_request(*args)

    def get_block_commitment(self, slot: int) -> types.RPCResponse:
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
        args = self._get_block_commitment_args(slot)
        return self._provider.make_request(*args)

    def get_block_time(self, slot: int) -> types.RPCResponse:
        """Fetch the estimated production time of a block.

        :param slot: Block, identified by Slot.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_block_time(5) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1598400007, 'id': 1}
        """
        args = self._get_block_time_args(slot)
        return self._provider.make_request(*args)

    def get_cluster_nodes(self) -> types.RPCResponse:
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
        return self._provider.make_request(self._get_cluster_nodes)

    def get_confirmed_block(
        self,
        slot: int,
        encoding: str = "json",
    ) -> types.RPCResponse:
        """Returns identity and transaction information about a confirmed block in the ledger.

        :param slot: Slot, as u64 integer.
        :param encoding: (optional) Encoding for the returned Transaction, either "json", "jsonParsed",
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
        args = self._get_confirmed_block_args(slot, encoding)
        return self._provider.make_request(*args)

    def get_confirmed_blocks(self, start_slot: int, end_slot: Optional[int] = None) -> types.RPCResponse:
        """Returns a list of confirmed blocks.

        :param start_slot: Start slot, as u64 integer.
        :param end_slot: (optional) End slot, as u64 integer.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_confirmed_blocks(5, 10) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': [5, 6, 7, 8, 9, 10], 'id': 1}
        """
        args = self._get_confirmed_blocks_args(start_slot, end_slot)
        return self._provider.make_request(*args)

    def get_confirmed_signature_for_address2(
        self, account: Union[str, Account, PublicKey], before: Optional[str] = None, limit: Optional[int] = None
    ) -> types.RPCResponse:
        """Returns confirmed signatures for transactions involving an address.

        Signatures are returned backwards in time from the provided signature or
        most recent confirmed block.

        :param account: Account to be queried.
        :param before: (optional) Start searching backwards from this transaction signature.
            If not provided the search starts from the top of the highest max confirmed block.
        :param limit: (optoinal) Maximum transaction signatures to return (between 1 and 1,000, default: 1,000).

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_confirmed_signature_for_address2("Vote111111111111111111111111111111111111111", limit=1) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': [{'err': None,
           'memo': None,
           'signature': 'v1BK8XcaPBzAGd7TB1K53pMdi6TBGe5CLCgx8cmZ4Bj63ZNvA6ca2QaxFpBFdvmpoFQ51VorBjifkBGLTDhwpqN',
           'slot': 4290}],
         'id': 2}
        """  # noqa: E501 # pylint: disable=line-too-long
        args = self._get_confirmed_signature_for_address2_args(account, before, limit)
        return self._provider.make_request(*args)

    def get_signatures_for_address(
        self, account: Union[str, Account, PublicKey], before: Optional[str] = None, limit: Optional[int] = None
    ) -> types.RPCResponse:
        """Returns confirmed signatures for transactions involving an address.

        Signatures are returned backwards in time from the provided signature or
        most recent confirmed block.

        :param account: Account to be queried.
        :param before: (optional) Start searching backwards from this transaction signature.
            If not provided the search starts from the top of the highest max confirmed block.
        :param limit: (optional) Maximum transaction signatures to return (between 1 and 1,000, default: 1,000).

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_signatures_for_address("Vote111111111111111111111111111111111111111", limit=1) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': [{'err': None,
           'memo': None,
           'signature': 'v1BK8XcaPBzAGd7TB1K53pMdi6TBGe5CLCgx8cmZ4Bj63ZNvA6ca2QaxFpBFdvmpoFQ51VorBjifkBGLTDhwpqN',
           'slot': 4290}],
         'id': 2}
        """  # noqa: E501 # pylint: disable=line-too-long
        args = self._get_signatures_for_address_args(account, before, limit)
        return self._provider.make_request(*args)

    def get_confirmed_transaction(self, tx_sig: str, encoding: str = "json") -> types.RPCResponse:
        """Returns transaction details for a confirmed transaction.

        :param tx_sig: Transaction signature as base-58 encoded string N encoding attempts to use program-specific
            instruction parsers to return more human-readable and explicit data in the
            `transaction.message.instructions` list.
        :param encoding: (optional) Encoding for the returned Transaction, either "json", "jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.

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
        args = self._get_confirmed_transaction_args(tx_sig, encoding)
        return self._provider.make_request(*args)

    def get_epoch_info(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns information about the current epoch.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

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
        args = self._get_epoch_info_args(commitment)
        return self._provider.make_request(*args)

    def get_epoch_schedule(self) -> types.RPCResponse:
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
        return self._provider.make_request(self._get_epoch_schedule)

    def get_fee_calculator_for_blockhash(
        self, blockhash: Union[str, Blockhash], commitment: Optional[Commitment] = None
    ) -> types.RPCResponse:
        """Returns the fee calculator associated with the query blockhash, or null if the blockhash has expired.

        :param blockhash: Blockhash to query as a Base58 encoded string.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_fee_calculator_for_blockhash("BaQSR194dC4dZaRxATtxYyEwDkk7VgqUY8NVNkub8HFZ") # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 7065},
          'value': {'feeCalculator': {'lamportsPerSignature': 5000}}},
         'id': 4}
        """  # noqa: E501 # pylint: disable=line-too-long
        args = self._get_fee_calculator_for_blockhash_args(blockhash, commitment)
        return self._provider.make_request(*args)

    def get_fee_rate_governor(self) -> types.RPCResponse:
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
        return self._provider.make_request(self._get_fee_rate_governor)

    def get_fees(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns a recent block hash from the ledger, a fee schedule and the last slot the blockhash will be valid.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_fees() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 7727},
          'value': {'blockhash': 'GGS6AEDqjF5irU6D6VQNherEZ2hckGaeBiVdfSZKg4gd',
           'feeCalculator': {'lamportsPerSignature': 5000},
           'lastValidSlot': 8027}},
         'id': 1}
        """
        args = self._get_fees_args(commitment)
        return self._provider.make_request(*args)

    def get_first_available_block(self) -> types.RPCResponse:
        """Returns the slot of the lowest confirmed block that has not been purged from the ledger.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_fees() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1, 'id': 2}
        """
        return self._provider.make_request(self._get_first_available_block)

    def get_genesis_hash(self) -> types.RPCResponse:
        """Returns the genesis hash.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_genesis_hash() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'EwF9gtehrrvPUoNticgmiEadAWzn4XeN8bNaNVBkS6S2',
         'id': 3}
        """
        return self._provider.make_request(self._get_genesis_hash)

    def get_identity(self) -> types.RPCResponse:
        """Returns the identity pubkey for the current node.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_identity() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'identity': 'LjvEBM78ufAikBfxqtj4RNiAECUi7Xqtz9k3QM3DzPk'},
         'id': 4}
        """
        return self._provider.make_request(self._get_identity)

    def get_inflation_governor(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns the current inflation governor.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

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
        args = self._get_inflation_governor_args(commitment)
        return self._provider.make_request(*args)

    def get_inflation_rate(self) -> types.RPCResponse:
        """Returns the specific inflation values for the current epoch.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_inflation_rate() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'epoch': 1,
          'foundation': 0.007499746885736559,
          'total': 0.14999493771473116,
          'validator': 0.1424951908289946},
         'id': 1}
        """
        return self._provider.make_request(self._get_inflation_rate)

    def get_largest_accounts(
        self, filter_opt: Optional[str] = None, commitment: Optional[Commitment] = None
    ) -> types.RPCResponse:
        """Returns the 20 largest accounts, by lamport balance.

        :param opt: Filter results by account type; currently supported: circulating|nonCirculating.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

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
        args = self._get_largest_accounts_args(filter_opt, commitment)
        return self._provider.make_request(*args)

    def get_leader_schedule(
        self, epoch: Optional[int] = None, commitment: Optional[Commitment] = None
    ) -> types.RPCResponse:
        """Returns the leader schedule for an epoch.

        :param epoch: Fetch the leader schedule for the epoch that corresponds to the provided slot.
            If unspecified, the leader schedule for the current epoch is fetched.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

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
        args = self._get_leader_schedule_args(epoch, commitment)
        return self._provider.make_request(*args)

    def get_minimum_balance_for_rent_exemption(
        self, usize: int, commitment: Optional[Commitment] = None
    ) -> types.RPCResponse:
        """Returns minimum balance required to make account rent exempt.

        :param usize: Account data length.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_minimum_balance_for_rent_exemption(50) # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1238880, 'id': 7}
        """
        args = self._get_minimum_balance_for_rent_exemption_args(usize, commitment)
        return self._provider.make_request(*args)

    def get_program_accounts(  # pylint: disable=too-many-arguments
        self,
        pubkey: Union[str, PublicKey],
        commitment: Optional[Commitment] = Finalized,
        encoding: Optional[str] = None,
        data_slice: Optional[types.DataSliceOpts] = None,
        data_size: Optional[int] = None,
        memcmp_opts: Optional[List[types.MemcmpOpts]] = None,
    ) -> types.RPCResponse:
        """Returns all accounts owned by the provided program Pubkey.

        :param pubkey: Pubkey of program, as base-58 encoded string or PublicKey object.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".
        :param encoding: (optional) Encoding for the returned Transaction, either jsonParsed",
            "base58" (slow), or "base64". If parameter not provided, the default encoding is JSON.
        :param data_slice: (optional) Limit the returned account data using the provided `offset`: <usize> and
            `length`: <usize> fields; only available for "base58" or "base64" encoding.
        :param data_size: (optional) Option to compare the program account data length with the provided data size.
        :param memcmp_opts: (optional) Options to compare a provided series of bytes with program account data at a particular offset.

        >>> solana_client = Client("http://localhost:8899")
        >>> memcmp_opts = [
        ...     MemcmpOpt(offset=4, bytes="3Mc6vR"),
        ... ]
        >>> solana_client.get_program_accounts("4Nd1mBQtrMJVYVfKf2PJy9NZUZdTAsp7D4xWLs4gDB4T", data_size=17, memcmp_opts=memcmp_opts) # doctest: +SKIP
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
        args = self._get_program_accounts_args(
            pubkey=pubkey,
            commitment=commitment,
            encoding=encoding,
            data_slice=data_slice,
            data_size=data_size,
            memcmp_opts=memcmp_opts,
        )
        return self._provider.make_request(*args)

    def get_recent_blockhash(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns a recent block hash from the ledger.

        Response also includes a fee schedule that can be used to compute the cost
        of submitting a transaction using it.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_recent_blockhash() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': {'context': {'slot': 1637},
          'value': {'blockhash': 'EALChog1mXQ9nEgEUQpWAtmA5UueUZvZiL16ZivmR7eb',
           'feeCalculator': {'lamportsPerSignature': 5000}}},
         'id': 2}
        """
        args = self._get_recent_blockhash_args(commitment)
        return self._provider.make_request(*args)

    def get_signature_statuses(
        self, signatures: List[Union[str, bytes]], search_transaction_history: bool = False
    ) -> types.RPCResponse:
        """Returns the statuses of a list of signatures.

        Unless the `searchTransactionHistory` configuration parameter is included, this method only
        searches the recent status cache of signatures, which retains statuses for all active slots plus
        `MAX_RECENT_BLOCKHASHES` rooted slots.

        :param signatures: An array of transaction signatures to confirm.
        :param search_transaction_history: If true, a Solana node will search its ledger cache for
            any signatures not found in the recent status cache.

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
        args = self._get_signature_statuses_args(signatures, search_transaction_history)
        return self._provider.make_request(*args)

    def get_slot(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns the current slot the node is processing.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_slot() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 7515, 'id': 1}
        """
        args = self._get_slot_args(commitment)
        return self._provider.make_request(*args)

    def get_slot_leader(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns the current slot leader.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_slot_leader() # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'EWj2cuEuVhi7RX81cnAY3TzpyFwnHzzVwvuTyfmxmhs3',
         'id': 1}
        """
        args = self._get_slot_leader_args(commitment)
        return self._provider.make_request(*args)

    def get_stake_activation(
        self, pubkey: Union[PublicKey, str], epoch: Optional[int] = None, commitment: Optional[Commitment] = None
    ) -> types.RPCResponse:
        """Returns epoch activation information for a stake account.

        :param pubkey: Pubkey of stake account to query, as base-58 encoded string or PublicKey object.
        :param epoch: (optional) Epoch for which to calculate activation details. If parameter not provided,
            defaults to current epoch.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_stake_activation() # doctest: +SKIP
        {'jsonrpc': '2.0','result': {'active': 124429280, 'inactive': 73287840, 'state': 'activating'}, 'id': 1}}
        """
        args = self._get_stake_activation_args(pubkey, epoch, commitment)
        return self._provider.make_request(*args)

    def get_supply(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns information about the current supply.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

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
        args = self._get_supply_args(commitment)
        return self._provider.make_request(*args)

    def get_token_account_balance(self, pubkey: Union[str, PublicKey], commitment: Optional[Commitment] = None):
        """Returns the token balance of an SPL Token account (UNSTABLE).

        :param pubkey: Pubkey of Token account to query, as base-58 encoded string or PublicKey object.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

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
        args = self._get_token_account_balance_args(pubkey, commitment)
        return self._provider.make_request(*args)

    def get_token_accounts_by_delegate(
        self,
        delegate: PublicKey,
        opts: types.TokenAccountOpts,
        commitment: Optional[Commitment] = None,
    ) -> types.RPCResponse:
        """Returns all SPL Token accounts by approved Delegate (UNSTABLE).

        :param pubkey: Public key of the delegate owner to query.
        :param opt: Token account option specifying at least one of `mint` or `program_id`.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".
        """
        args = self._get_token_accounts_by_delegate_args(delegate, opts, commitment)
        return self.__get_token_accounts(*args)

    def get_token_accounts_by_owner(
        self,
        owner: PublicKey,
        opts: types.TokenAccountOpts,
        commitment: Optional[Commitment] = None,
    ) -> types.RPCResponse:
        """Returns all SPL Token accounts by token owner (UNSTABLE).

        :param pubkey: Public key of the account owner to query.
        :param opt: Token account option specifying at least one of `mint` or `program_id`.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".
        """
        args = self._get_token_accounts_by_owner_args(owner, opts, commitment)
        return self.__get_token_accounts(*args)

    def __get_token_accounts(
        self,
        method: types.RPCMethod,
        pubkey: str,
        opts: types.TokenAccountOpts,
        commitment: Commitment,
    ) -> types.RPCResponse:
        args = self._get_token_accounts_args(method, pubkey, opts, commitment)
        return self._provider.make_request(*args)

    def get_token_largest_accounts(self, pubkey: Union[PublicKey, str]) -> types.RPCResponse:
        """Returns the 20 largest accounts of a particular SPL Token type (UNSTABLE)."""
        raise NotImplementedError("get_token_largbest_accounts not implemented")

    def get_token_supply(self, pubkey: Union[PublicKey, str]) -> types.RPCResponse:
        """Returns the total supply of an SPL Token type(UNSTABLE)."""
        raise NotImplementedError("get_token_supply not implemented")

    def get_transaction_count(self, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        """Returns the current Transaction count from the ledger.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_transaction_count() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 4554, 'id': 1}
        """
        args = self._get_transaction_count_args(commitment)
        return self._provider.make_request(*args)

    def get_minimum_ledger_slot(self) -> types.RPCResponse:
        """Returns the lowest slot that the node has information about in its ledger.

        This value may increase over time if the node is configured to purge older ledger data.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_minimum_ledger_slot() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': 1234, 'id': 1}
        """
        return self._provider.make_request(self._minimum_ledger_slot)

    def get_version(self) -> types.RPCResponse:
        """Returns the current solana versions running on the node.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.get_version() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': {'solana-core': '1.4.0 5332fcad'}, 'id': 1}
        """
        return self._provider.make_request(self._get_version)

    def get_vote_accounts(self, commitment: Optional[Commitment] = None):
        """Returns the account info and associated stake for all the voting accounts in the current bank.

        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

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
        args = self._get_vote_accounts_args(commitment)
        return self._provider.make_request(*args)

    def request_airdrop(
        self, pubkey: Union[PublicKey, str], lamports: int, commitment: Optional[Commitment] = None
    ) -> types.RPCResponse:
        """Requests an airdrop of lamports to a Pubkey.

        :param pubkey: Pubkey of account to receive lamports, as base-58 encoded string or public key object.
        :param lamports: Amout of lamports.
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> from solana.publickey import PublicKey
        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.request_airdrop(PublicKey(1), 10000) # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'uK6gbLbhnTEgjgmwn36D5BRTRkG4AT8r7Q162TLnJzQnHUZVL9r6BYZVfRttrhmkmno6Fp4VQELzL4AiriCo61U',
         'id': 1}
        """
        args = self._request_airdrop_args(pubkey, lamports, commitment)
        return self._provider.make_request(*args)

    def send_raw_transaction(self, txn: Union[bytes, str], opts: types.TxOpts = types.TxOpts()) -> types.RPCResponse:
        """Send a transaction that has already been signed and serialized into the wire format.

        :param txn: Fully-signed Transaction object, a fully sign transaction in wire format,
            or a fully transaction as base-64 encoded string.
        :param opts: (optional) Transaction options.

        Before submitting, the following preflight checks are performed (unless disabled with the `skip_preflight` option):

            - The transaction signatures are verified.

            - The transaction is simulated against the latest max confirmed bank and on failure an error
                will be returned. Preflight checks may be disabled if desired.

        >>> solana_client = Client("http://localhost:8899")
        >>> full_signed_tx_str = (
        ...     "AbN5XM+qw+7oOLsFw7goQSLBis7c1kXJFP6OF4w7YmQNhhbQYcyBiybKuOzzhV7McvoRP3Mey9AhXojtwDCdbwoBAAEDE5j2"
        ...     "LG0aRXxRumpLXz29L2n8qTIWIY3ImX5Ba9F9k8poq0Z3/7HyiU3QphU8Ix1F7ENq5TrmAUnb4V8y5LhwPwAAAAAAAAAAAAAA"
        ...     "AAAAAAAAAAAAAAAAAAAAAAAAAAAAg5YY9wG6fpuieuWYJd1ta7ZtFPbV0OriFRYdcYUaEGkBAgIAAQwCAAAAQEIPAAAAAAA=")
        >>> solana_client.send_raw_transaction(full_signed_tx_str)  # doctest: +SKIP
        {'jsonrpc': '2.0',
         'result': 'CMwyESM2NE74mghfbvsHJDERF7xMYKshwwm6VgH6GFqXzx8LfBFuP5ruccumfhTguha6seUHPpiHzzHUQXzq2kN',
         'id': 1}
        """  # noqa: E501 # pylint: disable=line-too-long
        args = self._send_raw_transaction_args(txn, opts)

        resp = self._provider.make_request(*args)
        if opts.skip_confirmation:
            return self._post_send(resp, self._provider)
        post_send_args = self._send_raw_transaction_post_send_args(resp, opts)
        return self.__post_send_with_confirm(*post_send_args)

    def send_transaction(
        self, txn: Transaction, *signers: Account, opts: types.TxOpts = types.TxOpts()
    ) -> types.RPCResponse:
        """Send a transaction.

        :param txn: Transaction object.
        :param signers: Signers to sign the transaction.
        :param opts: (optional) Transaction options.

        >>> from solana.account import Account
        >>> from solana.system_program import TransferParams, transfer
        >>> from solana.transaction import Transaction
        >>> sender, reciever = Account(1), Account(2)
        >>> txn = Transaction().add(transfer(TransferParams(
        ...     from_pubkey=sender.public_key(), to_pubkey=reciever.public_key(), lamports=1000)))
        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.send_transaction(txn, sender) # doctest: +SKIP
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
        return self.send_raw_transaction(txn.serialize(), opts=opts)

    def simulate_transaction(
        self, txn: Union[bytes, str, Transaction], sig_verify: bool = False, commitment: Optional[Commitment] = None
    ) -> types.RPCResponse:
        """Simulate sending a transaction.

        :param txn: A Transaction object, a transaction in wire format, or a transaction as base-64 encoded string
            The transaction must have a valid blockhash, but is not required to be signed.
        :param signer_verify: If true the transaction signatures will be verified (default: false).
        :param commitment: Bank state to query. It can be either "finalized", "confirmed" or "processed".

        >>> solana_client = Client("http://localhost:8899")
        >>> tx_str = (
        ...     "4hXTCkRzt9WyecNzV1XPgCDfGAZzQKNxLXgynz5QDuWWPSAZBZSHptvWRL3BjCvzUXRdKvHL2b7yGrRQcWyaqsaBCncVG7BF"
        ...     "ggS8w9snUts67BSh3EqKpXLUm5UMHfD7ZBe9GhARjbNQMLJ1QD3Spr6oMTBU6EhdB4RD8CP2xUxr2u3d6fos36PD98XS6oX8"
        ...     "TQjLpsMwncs5DAMiD4nNnR8NBfyghGCWvCVifVwvA8B8TJxE1aiyiv2L429BCWfyzAme5sZW8rDb14NeCQHhZbtNqfXhcp2t"
        ... )
        >>> solana_client.simulate_transaction(tx_str)  # doctest: +SKIP
        {'jsonrpc' :'2.0',
         'result': {'context': {'slot': 218},
         'value': {
             'err': null,
             'logs': ['BPF program 83astBRguLMdt2h5U1Tpdq5tjFoJ6noeGwaY3mDLVcri success']},
         'id':1}
        """  # noqa: E501 # pylint: disable=line-too-long
        args = self._simulate_transaction_args(txn, sig_verify, commitment)
        return self._provider.make_request(*args)

    def set_log_filter(self, log_filter: str) -> types.RPCResponse:
        """Sets the log filter on the validator.

        :param log_filter: The new log filter to use.

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.set_log_filter("solana_core=debug") # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': None, 'id': 1}
        """
        args = self._set_log_filter_args(log_filter)
        return self._provider.make_request(*args)

    def validator_exit(self) -> types.RPCResponse:
        """Request to have the validator exit.

        Validator must have booted with RPC exit enabled (`--enable-rpc-exit` parameter).

        >>> solana_client = Client("http://localhost:8899")
        >>> solana_client.validator_exit() # doctest: +SKIP
        {'jsonrpc': '2.0', 'result': true, 'id': 1}
        """
        return self._provider.make_request(self._validator_exit)

    def __post_send_with_confirm(self, resp: types.RPCResponse, conf_comm: Commitment) -> types.RPCResponse:
        resp = self._post_send(resp, self._provider)
        self._provider.logger.info(
            "Transaction sent to %s. Signature %s: ", self._provider.endpoint_uri, resp["result"]
        )
        return self.__confirm_transaction(resp["result"], conf_comm)

    def __confirm_transaction(self, tx_sig: str, commitment: Optional[Commitment] = None) -> types.RPCResponse:
        # TODO: Use websockets and check confirmation with onSignature subscription.
        TIMEOUT = 30  # 30 seconds  pylint: disable=invalid-name
        elapsed_time = 0
        while elapsed_time < TIMEOUT:
            sleep_time = 3
            if not elapsed_time:
                sleep_time = 7 if (commitment or self._commitment) == Finalized else sleep_time
                sleep(sleep_time)
            else:
                sleep(sleep_time)

            resp = self.get_confirmed_transaction(tx_sig)
            if resp["result"]:
                break
            elapsed_time += sleep_time

        if not resp["result"]:
            raise Exception("Unable to confirm transaction %s" % tx_sig)
        err = resp.get("error") or resp["result"].get("meta").get("err")
        if err:
            self._provider.logger.error("Transaction error: %s", err)

        return resp
