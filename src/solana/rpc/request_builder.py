from dataclasses import dataclass
from typing import Any, Optional, Union, Literal
from jsonrpcclient import request

from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solana.rpc import types
from solana.transaction import TransactionSignature

MentionsFilter = dict[Literal["mentions"], str]


@dataclass
class AccountSubscribe:
    pubkey: PublicKey
    encoding: Optional[str] = None
    commitment: Optional[Commitment] = None

    def to_request(self) -> dict[str, Any]:
        dict_params = {}
        if self.encoding is not None:
            dict_params["encoding"] = self.encoding
        if self.commitment is not None:
            dict_params["commitment"] = self.commitment
        params = [str(self.pubkey)]
        if dict_params:
            params.append(dict_params)
        return request("accountSubscribe", params=params)


class LogsSubsrcibeFilter:
    ALL = "all"
    ALL_WITH_VOTES = "allWithVotes"

    @staticmethod
    def mentions(pubkeys: list[PublicKey]) -> MentionsFilter:
        return {"mentions": [str(p) for p in pubkeys]}


@dataclass
class LogsSubscribe:
    filter_: Union[str, MentionsFilter]
    commitment: Optional[Commitment] = None

    def to_request(self) -> dict[str, Any]:
        dict_params = {}
        if self.commitment is not None:
            dict_params["commitment"] = self.commitment
        params = [self.filter_]
        if dict_params:
            params.append(dict_params)
        return request("logsSubscribe", params=params)


@dataclass
class ProgramSubscribe:
    program_id: PublicKey
    encoding: Optional[str] = None
    commitment: Optional[Commitment] = None
    data_size: Optional[int] = None
    memcmp_opts: Optional[list[types.MemcmpOpts]] = None

    def to_request(self) -> dict[str, Any]:
        dict_params = {}
        if self.commitment is not None:
            dict_params["commitment"] = self.commitment
        filters = []
        for opt in [] if not self.memcmp_opts else self.memcmp_opts:
            filters.append({"memcmp": dict(opt._asdict())})
        if self.data_size:
            filters.append({"dataSize": self.data_size})
        if filters:
            dict_params["filters"] = filters
        params = [str(self.program_id)]
        if dict_params:
            params.append(dict_params)
        return request("programSubscribe", params=params)


@dataclass
class SignatureSubscribe:
    signature: TransactionSignature
    commitment: Optional[Commitment] = None

    def to_request(self) -> dict[str, Any]:
        dict_params = {}
        if self.commitment is not None:
            dict_params["commitment"] = self.commitment
        params = [self.signature]
        if dict_params:
            params.append(dict_params)
        return request("signatureSubscribe", params=params)


@dataclass
class SlotSubscribe:
    @staticmethod
    def to_request() -> dict[str, Any]:
        return request("slotSubscribe")


@dataclass
class SlotsUpdatesSubscribe:
    @staticmethod
    def to_request() -> dict[str, Any]:
        return request("slotsUpdatesSubscribe")


@dataclass
class RootSubscribe:
    @staticmethod
    def to_request() -> dict[str, Any]:
        return request("rootSubscribe")


@dataclass
class VoteSubscribe:
    @staticmethod
    def to_request() -> dict[str, Any]:
        return request("voteSubscribe")
