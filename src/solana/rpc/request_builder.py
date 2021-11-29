from typing import Any, Optional, Union, Literal, List, Dict
from jsonrpcclient import request

from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solana.rpc import types
from solana.transaction import TransactionSignature

MentionsFilter = Dict[Literal["mentions"], str]


class RequestBody:
    def __init__(self, name: str) -> None:
        self.name = name

    def to_request(self) -> Dict[str, Any]:
        return request(self.name)


class HasDictParams(RequestBody):
    def __init__(self, name: str, dict_params: Optional[Dict[str, str]] = None) -> None:
        super().__init__(name)
        self.dict_params: Dict[str, str] = {} if dict_params is None else dict_params

    def to_request(self) -> Dict[str, Any]:
        return request(self.name, params=self.dict_params)


class Unsubscribe(RequestBody):
    def __init__(self, name: str, subscription: int) -> None:
        super().__init__(name)
        self.subscription = subscription

    def to_request(self) -> Dict[str, Any]:
        return request(self.name, params=[self.subscription])


class HasEncoding(HasDictParams):
    def __init__(self, name: str, encoding: Optional[str] = None) -> None:
        dict_params: Optional[Dict[str, str]] = None if encoding is None else {"encoding": encoding}
        super().__init__(name, dict_params)


class HasCommitment(HasDictParams):
    def __init__(self, name: str, commitment: Optional[Commitment] = None) -> None:
        dict_params: Optional[Dict[str, str]] = None if commitment is None else {"commitment": commitment}
        super().__init__(name, dict_params)


class HasCommitmentAndEncoding(HasCommitment):
    def __init__(self, name: str, commitment: Optional[Commitment] = None, encoding: Optional[str] = None) -> None:
        super().__init__(name, commitment)
        if encoding is not None:
            self.dict_params["encoding"] = encoding


class HasPositionalParamAndCommitmentAndEncoding(HasCommitmentAndEncoding):
    def __init__(
        self, name: str, positional_param: Any, commitment: Optional[Commitment] = None, encoding: Optional[str] = None
    ) -> None:
        super().__init__(name, commitment, encoding)
        self.positional_param = positional_param

    def to_request(self) -> Dict[str, Any]:
        return request(self.name, params=[self.positional_param, self.dict_params])


class AccountSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    def __init__(
        self, pubkey: PublicKey, commitment: Optional[Commitment] = None, encoding: Optional[str] = None
    ) -> None:
        super().__init__(
            name="accountSubscribe", positional_param=str(pubkey), commitment=commitment, encoding=encoding
        )


class AccountUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("accountUnsubscribe", subscription)


class LogsSubsrcibeFilter:
    ALL = "all"
    ALL_WITH_VOTES = "allWithVotes"

    @staticmethod
    def mentions(pubkeys: List[PublicKey]) -> MentionsFilter:
        return {"mentions": [str(p) for p in pubkeys]}


class LogsSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    def __init__(
        self,
        filter_: Union[str, MentionsFilter],
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
    ) -> None:
        super().__init__(name="logsSubscribe", positional_param=filter_, commitment=commitment, encoding=encoding)


class LogsUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("logsUnsubscribe", subscription)


class ProgramSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    def __init__(
        self,
        program_id: PublicKey,
        encoding: Optional[str] = None,
        commitment: Optional[Commitment] = None,
        data_size: Optional[int] = None,
        memcmp_opts: Optional[List[types.MemcmpOpts]] = None,
    ) -> None:
        super().__init__(
            name="programSubscribe", positional_param=str(program_id), encoding=encoding, commitment=commitment
        )
        filters = []
        for opt in [] if not memcmp_opts else memcmp_opts:
            filters.append({"memcmp": dict(opt._asdict())})
        if data_size:
            filters.append({"dataSize": data_size})
        if filters:
            self.dict_params["filters"] = filters


class ProgramUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("programUnsubscribe", subscription)


class SignatureSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    def __init__(
        self,
        name: str,
        signature: TransactionSignature,
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
    ) -> None:
        super().__init__(
            name="signatureSubscribe", positional_param=signature, commitment=commitment, encoding=encoding
        )


class SignatureUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("signatureUnsubscribe", subscription)


class SlotSubscribe(RequestBody):
    def __init__(self) -> None:
        super().__init__("slotSubscribe")


class SlotUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("slotUnsubscribe", subscription)


class SlotsUpdatesSubscribe(RequestBody):
    def __init__(self) -> None:
        super().__init__("slotsUpdatesSubscribe")


class SlotsUpdatesUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("slotsUpdatesUnsubscribe", subscription)


class RootSubscribe(RequestBody):
    def __init__(self) -> None:
        super().__init__("rootSubscribe")


class RootUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("rootUnsubscribe", subscription)


class VoteSubscribe(RequestBody):
    def __init__(self) -> None:
        super().__init__("voteSubscribe")


class VoteUnsubscribe(Unsubscribe):
    def __init__(self, subscription: int) -> None:
        super().__init__("VoteUnsubscribe", subscription)
