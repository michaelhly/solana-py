"""Commitment options.

Solana nodes choose which bank state to query based on a commitment requirement set by the client.

In descending order of commitment (most finalized to least finalized), clients may specify:
"""

from enum import StrEnum
from typing import Literal

from typing_extensions import assert_never


class Commitment(StrEnum):
    """Enumeration of commitment levels for RPC requests.

    Members:
        PROCESSED: The node will query its most recent block. Note that the block may not be complete.
        CONFIRMED: The node will query the most recent block that has been voted on by supermajority of the cluster.
        FINALIZED: The node will query the most recent block confirmed by supermajority of the cluster as finalized.
    """

    PROCESSED = "processed"
    """The node will query its most recent block. Note that the block may not be complete."""

    CONFIRMED = "confirmed"
    """The node will query the most recent block that has been voted on by supermajority of the cluster.

    - It incorporates votes from gossip and replay.
    - It does not count votes on descendants of a block, only direct votes on that block.
    - This confirmation level also upholds "optimistic confirmation" guarantees in release 1.3 and onwards.
    """

    FINALIZED = "finalized"
    """The node will query the most recent block confirmed by supermajority of the cluster as having reached maximum
    lockout, meaning the cluster has recognized this block as finalized."""


# Backward-compatibility aliases for old code that uses the lowercase module-level names
Finalized = Commitment.FINALIZED
Confirmed = Commitment.CONFIRMED
Processed = Commitment.PROCESSED


def get_commitment_score(commitment: Commitment) -> int:
    """Return an integer score for a commitment level, with higher scores meaning more finalized.

    Args:
        commitment: The commitment level to score.

    Returns:
        An integer score (2 for FINALIZED, 1 for CONFIRMED, 0 for PROCESSED).

    Example:
        >>> get_commitment_score(Commitment.FINALIZED)
        2
        >>> get_commitment_score(Commitment.CONFIRMED)
        1
        >>> get_commitment_score(Commitment.PROCESSED)
        0
    """
    match commitment:
        case Commitment.FINALIZED:
            return 2
        case Commitment.CONFIRMED:
            return 1
        case Commitment.PROCESSED:
            return 0
        case _:
            assert_never(commitment)


def commitment_comparator(a: Commitment, b: Commitment) -> Literal[-1, 0, 1]:
    """Compare two commitment levels by their degree of finalization.

    Args:
        a: First commitment level.
        b: Second commitment level.

    Returns:
        -1 if ``a`` is less finalized than ``b``,
            0 if they are equal,
            1 if ``a`` is more finalized than ``b``.

    Example:
        >>> commitment_comparator(Commitment.FINALIZED, Commitment.PROCESSED)
        1
        >>> commitment_comparator(Commitment.PROCESSED, Commitment.CONFIRMED)
        -1
        >>> commitment_comparator(Commitment.CONFIRMED, Commitment.CONFIRMED)
        0
    """
    if a is b:
        return 0
    return -1 if get_commitment_score(a) < get_commitment_score(b) else 1
