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
class SlotBase:
    slot: int


@dataclass
class SlotAndTimestampBase(SlotBase):
    timestamp: int


@dataclass
class FirstShredReceived(SlotAndTimestampBase):
    type: Literal["firstShredReceived"]


@dataclass
class Completed(SlotAndTimestampBase):
    type: Literal["completed"]


@dataclass
class CreatedBank(SlotAndTimestampBase):
    parent: int
    type: Literal["createdBank"]


@dataclass
class SlotTransactionStats:
    num_transaction_entries: int = field(metadata=alias("numTransactionEntries"))
    num_successful_transactions: int = field(metadata=alias("numSuccessfulTransactions"))
    num_failed_transactions: int = field(metadata=alias("numFailedTransactions"))
    max_transactions_per_entry: int = field(metadata=alias("maxTransactionsPerEntry"))


@dataclass
class Frozen(SlotAndTimestampBase):
    stats: SlotTransactionStats
    type: Literal["frozen"]


@dataclass
class Dead(SlotAndTimestampBase):
    err: str
    type: Literal["dead"]


@dataclass
class OptimisticConfirmation(SlotAndTimestampBase):
    type: Literal["optimisticConfirmation"]


@dataclass
class Root(SlotAndTimestampBase):
    type: Literal["root"]


SlotsUpdatesItem = Union[FirstShredReceived, Completed, CreatedBank, Frozen, Dead, OptimisticConfirmation, Root]


@dataclass
class SlotsUpdatesNotification(SubscriptionNotification):
    result: SlotsUpdatesItem
