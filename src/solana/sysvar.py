"""Synthetic accounts that allow programs to access certain network states."""
import solders.sysvar as sv
from solders.pubkey import Pubkey

SYSVAR_CLOCK_PUBKEY: Pubkey = sv.CLOCK
"""Public key of the synthetic account that serves the current network time."""

SYSVAR_RECENT_BLOCKHASHES_PUBKEY: Pubkey = sv.RECENT_BLOCKHASHES
"""Public key of the synthetic account that serves recent blockhashes."""

SYSVAR_RENT_PUBKEY: Pubkey = sv.RENT
"""Public key of the synthetic account that serves the network fee resource consumption."""

SYSVAR_REWARDS_PUBKEY: Pubkey = sv.REWARDS
"""Public key of the synthetic account that serves the network rewards."""

SYSVAR_STAKE_HISTORY_PUBKEY: Pubkey = sv.STAKE_HISTORY
"""Public key of the synthetic account that serves the stake history."""

SYSVAR_EPOCH_SCHEDULE_PUBKEY: Pubkey = sv.EPOCH_SCHEDULE
"""The EpochSchedule sysvar contains epoch scheduling constants that are set in genesis, and enables calculating the
number of slots in a given epoch, the epoch for a given slot, etc. (Note: the epoch schedule is distinct from the
`leader schedule <https://docs.solana.com/terminology#leader-schedule>`_).
"""

SYSVAR_INSTRUCTIONS_PUBKEY: Pubkey = sv.INSTRUCTIONS
"""
The Instructions sysvar contains the serialized instructions in a Message while that Message is being processed.
This allows program instructions to reference other instructions in the same transaction.
Read more information on `instruction introspection
<https://docs.solana.com/implemented-proposals/instruction_introspection>`_.
"""

SYSVAR_SLOT_HASHES_PUBKEY: Pubkey = sv.SLOT_HASHES
"""The SlotHashes sysvar contains the most recent hashes of the slot's parent banks. It is updated every slot."""
