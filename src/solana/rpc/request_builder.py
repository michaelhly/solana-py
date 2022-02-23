# pylint: disable=too-few-public-methods
"""This module contains code for building RPC requests."""
from typing import Any, Optional, Union, Literal, List, Dict
from jsonrpcclient import request

from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solana.rpc import types
from solana.transaction import TransactionSignature

MentionsFilter = Dict[Literal["mentions"], List[str]]


class RequestBody:
    """Base class for RPC request data."""

    def __init__(self, name: str) -> None:
        """Init."""
        self.name = name

    def to_request(self) -> Dict[str, Any]:
        """Convert to a request dict."""
        return request(self.name)


class HasDictParams(RequestBody):
    """Base class for PRC requests with dictionary params."""

    def __init__(self, name: str, dict_params: Optional[Dict[str, str]] = None) -> None:
        """Init."""
        super().__init__(name)
        self.dict_params: Dict[str, Any] = {} if dict_params is None else dict_params

    def to_request(self) -> Dict[str, Any]:
        """Convert to a request dict."""
        return request(self.name, params=self.dict_params)


class Unsubscribe(RequestBody):
    """RPC pubsub unsubscribe base class."""

    def __init__(self, name: str, subscription: int) -> None:
        """Init."""
        super().__init__(name)
        self.subscription = subscription

    def to_request(self) -> Dict[str, Any]:
        """Convert to a request dict."""
        return request(self.name, params=[self.subscription])


class HasEncoding(HasDictParams):
    """Base class for RPC request that takes an encoding param."""

    def __init__(self, name: str, encoding: Optional[str] = None) -> None:
        """Init."""
        dict_params: Optional[Dict[str, str]] = None if encoding is None else {"encoding": encoding}
        super().__init__(name, dict_params)


class HasCommitment(HasDictParams):
    """Base class for RPC request that takes a commitment param."""

    def __init__(self, name: str, commitment: Optional[Commitment] = None) -> None:
        """Init."""
        dict_params: Optional[Dict[str, str]] = None if commitment is None else {"commitment": commitment}
        super().__init__(name, dict_params)


class HasCommitmentAndEncoding(HasCommitment):
    """Base class for RPC request that takes encoding and commitment params."""

    def __init__(self, name: str, commitment: Optional[Commitment] = None, encoding: Optional[str] = None) -> None:
        """Init."""
        super().__init__(name, commitment)
        if encoding is not None:
            self.dict_params["encoding"] = encoding


class HasPositionalParamAndCommitmentAndEncoding(HasCommitmentAndEncoding):
    """Base class for RPC request that takes a positional param as well as encoding and commitment params."""

    def __init__(
        self, name: str, positional_param: Any, commitment: Optional[Commitment] = None, encoding: Optional[str] = None
    ) -> None:
        """Init."""
        super().__init__(name, commitment, encoding)
        self.positional_param = positional_param

    def to_request(self) -> Dict[str, Any]:
        """Convert to a request dict."""
        return request(self.name, params=[self.positional_param, self.dict_params])


class AccountSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    """Request body for accountSubscribe."""

    def __init__(
        self, pubkey: PublicKey, commitment: Optional[Commitment] = None, encoding: Optional[str] = None
    ) -> None:
        """Init."""
        super().__init__(
            name="accountSubscribe", positional_param=str(pubkey), commitment=commitment, encoding=encoding
        )


class AccountUnsubscribe(Unsubscribe):
    """Request body for accountUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("accountUnsubscribe", subscription)


class LogsSubscribeFilter:
    """Different kinds of filter for logSubscribe."""

    ALL = "all"
    ALL_WITH_VOTES = "allWithVotes"

    @staticmethod
    def mentions(pubkey: PublicKey) -> MentionsFilter:
        """Filter for logs mentioning the given pubkey."""
        return {"mentions": [str(pubkey)]}


class LogsSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    """Request body for logsSubscribe."""

    def __init__(
        self,
        filter_: Union[str, MentionsFilter],
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
    ) -> None:
        """Init."""
        super().__init__(name="logsSubscribe", positional_param=filter_, commitment=commitment, encoding=encoding)


class LogsUnsubscribe(Unsubscribe):
    """Request body for logsUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("logsUnsubscribe", subscription)


class ProgramSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    """Request body for programSubscribe."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        program_id: PublicKey,
        commitment: Optional[Commitment] = None,
        encoding: Optional[str] = None,
        data_size: Optional[int] = None,
        memcmp_opts: Optional[List[types.MemcmpOpts]] = None,
    ) -> None:
        """Init.

        Args:
            program_id: The program ID.
            commitment: Commitment level to use.
            encoding: Encoding to use.
            data_size: Data size filter.
            memcmp_opts: memcmp options.
        """
        super().__init__(
            name="programSubscribe", positional_param=str(program_id), encoding=encoding, commitment=commitment
        )
        filters = []
        for opt in [] if not memcmp_opts else memcmp_opts:
            filters.append({"memcmp": dict(opt._asdict())})
        if data_size:
            filters.append({"dataSize": data_size})  # type: ignore
        if filters:
            self.dict_params["filters"] = filters


class ProgramUnsubscribe(Unsubscribe):
    """Request body for programUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("programUnsubscribe", subscription)


class SignatureSubscribe(HasPositionalParamAndCommitmentAndEncoding):
    """Request body for signatureSubscribe."""

    def __init__(
        self,
        signature: TransactionSignature,
        commitment: Optional[Commitment] = None,
    ) -> None:
        """Init.

        Args:
            signature: Transaction signature to subscribe to.
            commitment: Commitment level to use.
        """
        super().__init__(name="signatureSubscribe", positional_param=signature, commitment=commitment)


class SignatureUnsubscribe(Unsubscribe):
    """Request body for signatureUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("signatureUnsubscribe", subscription)


class SlotSubscribe(RequestBody):
    """Request body for slotSubscribe."""

    def __init__(self) -> None:
        """Init."""
        super().__init__("slotSubscribe")


class SlotUnsubscribe(Unsubscribe):
    """Request body for slotUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("slotUnsubscribe", subscription)


class SlotsUpdatesSubscribe(RequestBody):
    """Request body for slotsUpdatesSubscribe."""

    def __init__(self) -> None:
        """Init."""
        super().__init__("slotsUpdatesSubscribe")


class SlotsUpdatesUnsubscribe(Unsubscribe):
    """Request body for slotUpdatesUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("slotsUpdatesUnsubscribe", subscription)


class RootSubscribe(RequestBody):
    """Request body for rootSubscribe."""

    def __init__(self) -> None:
        """Init."""
        super().__init__("rootSubscribe")


class RootUnsubscribe(Unsubscribe):
    """Request body for rootUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("rootUnsubscribe", subscription)


class VoteSubscribe(RequestBody):
    """Request body for voteSubscribe."""

    def __init__(self) -> None:
        """Init."""
        super().__init__("voteSubscribe")


class VoteUnsubscribe(Unsubscribe):
    """Request body for voteUnsubscribe."""

    def __init__(self, subscription: int) -> None:
        """Init."""
        super().__init__("VoteUnsubscribe", subscription)
