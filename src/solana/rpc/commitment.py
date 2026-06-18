"""Commitment options.

Solana nodes choose which bank state to query based on a commitment requirement set by the client.

In descending order of commitment (most finalized to least finalized), clients may specify:
"""

import warnings
from typing import NewType

Commitment = NewType("Commitment", str)
"""Type for commitment."""

Finalized = Commitment("finalized")
"""The node will query the most recent block confirmed by supermajority of the cluster as having reached maximum
 lockout, meaning the cluster has recognized this block as finalized."""

Confirmed = Commitment("confirmed")
"""The node will query the most recent block that has been voted on by supermajority of the cluster.

- It incorporates votes from gossip and replay.
- It does not count votes on descendants of a block, only direct votes on that block.
- This confirmation level also upholds "optimistic confirmation" guarantees in release 1.3 and onwards.
"""

Processed = Commitment("processed")
"""The node will query its most recent block. Note that the block may not be complete."""

_DEPRECATED = {
    "Max": Commitment("max"),
    "Root": Commitment("root"),
    "Single": Commitment("singleGossip"),
    "Recent": Commitment("recent"),
}


def __getattr__(name: str) -> Commitment:
    if name in _DEPRECATED:
        warnings.warn(f"Commitment.{name} is deprecated.", DeprecationWarning, stacklevel=2)
        return _DEPRECATED[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
