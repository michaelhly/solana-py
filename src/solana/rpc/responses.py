"""This module contains code for parsing RPC responses."""
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
    """Container for possible transaction errors."""

    err: TransactionErrorResult


@dataclass
class Context:
    """RPC result context."""

    slot: int


@dataclass
class WithContext:
    """Base class for RPC result including context."""

    context: Context


@dataclass
class AccountInfo:
    """Account information."""

    lamports: int
    owner: PublicKey
    data: Union[Literal[""], Tuple[str, str], Dict[str, Any]]
    executable: bool
    rent_epoch: int = field(metadata=alias("rentEpoch"))


@dataclass
class AccountInfoAndContext(WithContext):
    """Account info and RPC result context."""

    value: AccountInfo


@dataclass
class SubscriptionNotificationBase:
    """Base class for RPC subscription notifications."""

    subscription: int
    result: Any


@dataclass
class AccountNotification(SubscriptionNotificationBase):
    """Account subscription notification."""

    result: AccountInfoAndContext


@dataclass
class LogItem(TransactionErr):
    """Container for logs from logSubscribe."""

    signature: TransactionSignature
    logs: Optional[List[str]]


@dataclass
class LogItemAndContext(WithContext):
    """Log item with RPC result context."""

    value: LogItem


@dataclass
class LogsNotification(SubscriptionNotificationBase):
    """Logs subscription notification."""

    result: LogItemAndContext


@dataclass
class ProgramAccount:
    """Program account pubkey and account info."""

    pubkey: PublicKey
    account: AccountInfo


@dataclass
class ProgramAccountAndContext(WithContext):
    """Program subscription data with RPC result context."""

    value: ProgramAccount


@dataclass
class ProgramNotification(SubscriptionNotificationBase):
    """Program subscription notification."""

    result: ProgramAccountAndContext


@dataclass
class SignatureErrAndContext(WithContext):
    """Signature subscription error info with RPC result context."""

    value: TransactionErr


@dataclass
class SignatureNotification(SubscriptionNotificationBase):
    """Signature subscription notification."""

    result: SignatureErrAndContext


@dataclass
class SlotBase:
    """Base class for slot container."""

    slot: int


@dataclass
class SlotInfo(SlotBase):
    """Slot info."""

    parent: int
    root: int


@dataclass
class SlotNotification(SubscriptionNotificationBase):
    """Slot subscription notification."""

    result: SlotInfo


@dataclass
class RootNotification(SubscriptionNotificationBase):
    """Root subscription notification."""

    result: int


@dataclass
class SlotAndTimestampBase(SlotBase):
    """Base class for a slot with timestamp."""

    timestamp: int


@dataclass
class FirstShredReceived(SlotAndTimestampBase):
    """First shread received update."""

    type: Literal["firstShredReceived"]


@dataclass
class Completed(SlotAndTimestampBase):
    """Slot completed update."""

    type: Literal["completed"]


@dataclass
class CreatedBank(SlotAndTimestampBase):
    """Created bank update."""

    parent: int
    type: Literal["createdBank"]


@dataclass
class SlotTransactionStats:
    """Slot transaction stats."""

    num_transaction_entries: int = field(metadata=alias("numTransactionEntries"))
    num_successful_transactions: int = field(metadata=alias("numSuccessfulTransactions"))
    num_failed_transactions: int = field(metadata=alias("numFailedTransactions"))
    max_transactions_per_entry: int = field(metadata=alias("maxTransactionsPerEntry"))


@dataclass
class Frozen(SlotAndTimestampBase):
    """Slot frozen update."""

    stats: SlotTransactionStats
    type: Literal["frozen"]


@dataclass
class Dead(SlotAndTimestampBase):
    """Dead slot update."""

    err: str
    type: Literal["dead"]


@dataclass
class OptimisticConfirmation(SlotAndTimestampBase):
    """Optimistic confirmation update."""

    type: Literal["optimisticConfirmation"]


@dataclass
class Root(SlotAndTimestampBase):
    """Root update."""

    type: Literal["root"]


SlotsUpdatesItem = Union[FirstShredReceived, Completed, CreatedBank, Frozen, Dead, OptimisticConfirmation, Root]


@dataclass
class SlotsUpdatesNotification(SubscriptionNotificationBase):
    """Slots updates notification."""

    result: SlotsUpdatesItem


@dataclass
class VoteItem:
    """Vote data."""

    hash: str
    slots: List[int]
    timestamp: Optional[int]


@dataclass
class VoteNotification(SubscriptionNotificationBase):
    """Vote update notification."""

    result: VoteItem


SubscriptionNotification = Union[
    AccountNotification,
    LogsNotification,
    ProgramNotification,
    SignatureNotification,
    SlotNotification,
    RootNotification,
    SlotsUpdatesNotification,
    VoteNotification,
]
