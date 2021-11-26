from dataclasses import dataclass
from typing import Any, Optional, Union, Literal
from jsonrpcclient import request

from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solana.rpc import types
from solana.transaction import TransactionSignature

MentionsFilter = dict[Literal["mentions"], str]


class HasDictParams:
    def __init__(self, name: str, dict_params: Optional[dict[str, str]] = None) -> None:
        self.name = name
        self.dict_params: dict[str, str] = {} if dict_params is None else dict_params

    def to_request(self) -> dict[str, Any]:
        return request(self.name, params=self.dict_params)


class HasEncoding(HasDictParams):
    def __init__(self, name: str, encoding: Optional[str] = None) -> None:
        dict_params: Optional[dict[str, str]] = None if encoding is None else {"encoding": encoding}
        super().__init__(name, dict_params)


class HasCommitment(HasDictParams):
    def __init__(self, name: str, commitment: Optional[Commitment] = None) -> None:
        dict_params: Optional[dict[str, str]] = None if commitment is None else {"commitment": commitment}
        super().__init__(name, dict_params)


class HasCommitmentAndEncoding(HasCommitment):
    def __init__(self, name: str, commitment: Optional[Commitment] = None, encoding: Optional[str] = None) -> None:
        super().__init__(name, commitment)
        if encoding is not None:
            self.dict_params["encoding"] = encoding

class HasListParamAndDictParams(HasCommitmentAndEncoding):
    def __init__(self, name: str, list_param: list, commitment: Optional[Commitment] = None, encoding: Optional[str] = None) -> None:
        super
class AccountSubscribe(HasCommitmentAndEncoding):
    def __init__(self, name: str, pubkey: PublicKey, commitment: Optional[Commitment] = None, encoding: Optional[str] = None) -> None:


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
