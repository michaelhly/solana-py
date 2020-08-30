"""Synthetic accounts that allow programs to access certain network states."""
from solana.publickey import PublicKey

SYSVAR_CLOCK_PUBKEY: PublicKey = PublicKey("SysvarC1ock11111111111111111111111111111111")
"""Public key of the synthetic account that serves the current network time."""

SYSVAR_RECENT_BLOCKHASHES_PUBKEY: PublicKey = PublicKey("SysvarRecentB1ockHashes11111111111111111111")
"""Public key of the synthetic account that serves recent blockhashes."""

SYSVAR_RENT_PUBKEY: PublicKey = PublicKey("SysvarRent111111111111111111111111111111111")
"""Public key of the synthetic account that serves the network fee resource consumption."""

SYSVAR_REWARDS_PUBKEY: PublicKey = PublicKey("SysvarRewards111111111111111111111111111111")
"""Public key of the synthetic account that serves the network rewards."""

SYSVAR_STAKE_HISTORY_PUBKEY: PublicKey = PublicKey("SysvarStakeHistory1111111111111111111111111")
"""Public key of the synthetic account that serves the stake history."""
