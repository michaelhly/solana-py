from dataclasses import dataclass, field
from typing import Union, Tuple, Any, Dict, List, Optional, Literal

from apischema import alias
from apischema.conversions import as_str


from solana.publickey import PublicKey
from solana.transaction import TransactionSignature

as_str(PublicKey)


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
class LogItem:
    signature: TransactionSignature
    err: Optional[dict]
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
