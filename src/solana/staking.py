from solana.publickey import PublicKey
from typing import NamedTuple


class Authorized(NamedTuple):
    """Staking account authority info."""
    staker: PublicKey
    """"""
    withdrawer: PublicKey
    """"""


class Lockup(NamedTuple):
    """Stake account lockup info."""
    unix_timestamp: int
    """"""
    epoch: int
    """"""
    custodian: PublicKey
