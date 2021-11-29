from dataclasses import dataclass, field
from typing import Union, Tuple, Any, Dict, List, Optional, Literal

from apischema import alias
from apischema.conversions import as_str


from solana.publickey import PublicKey
from solana.transaction import TransactionSignature

as_str(PublicKey)

TransactionErrorResult = Optional[dict]


@dataclass
class TransactionErr:
    err: TransactionErrorResult


@dataclass
class Context:
    slot: int


@dataclass
class WithContext:
    context: Context


@dataclass
class AccountInfo:
    lamports: int
    owner: PublicKey
    data: Union[Literal[""], Tuple[str, str], Dict[str, Any]]
    executable: bool
    rent_epoch: int = field(metadata=alias("rentEpoch"))


@dataclass
class AccountInfoAndContext(WithContext):
    value: AccountInfo


@dataclass
class SubscriptionNotification:
    subscription: int


@dataclass
class AccountNotification(SubscriptionNotification):
    result: AccountInfoAndContext


@dataclass
class LogItem(TransactionErr):
    signature: TransactionSignature
    logs: Optional[List[str]]


@dataclass
class LogItemAndContext(WithContext):
    value: LogItem


@dataclass
class LogsNotification(SubscriptionNotification):
    result: LogItemAndContext


@dataclass
class ProgramAccount:
    pubkey: PublicKey
    account: AccountInfo


@dataclass
class ProgramAccountAndContext(WithContext):
    value: ProgramAccount


@dataclass
class ProgramNotification(SubscriptionNotification):
    result: ProgramAccountAndContext


@dataclass
class SignatureErrAndContext(WithContext):
    value: TransactionErr


@dataclass
class SignatureNotification(SubscriptionNotification):
    result: SignatureErrAndContext


@dataclass
class SlotItem:
    parent: int
    root: int
    slot: int


@dataclass
class SlotNotification(SubscriptionNotification):
    result: SlotItem


@dataclass
class RootNotification(SubscriptionNotification):
    result: int


@dataclass
class SlotsUpdatesItem:
    slot: int
    timestamp: int
    type: Literal["firstShredReceived", "completed", "createdBank", "frozen", "dead", "optimisticConfirmation", "root"]
    parent: Optional[int] = None


@dataclass
class SlotsUpdatesNotification(SubscriptionNotification):
    result: SlotsUpdatesItem
