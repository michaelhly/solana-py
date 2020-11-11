"""Commitment options.

Solana nodes choose which bank state to query based on a commitment requirement set by the client.

In descending order of commitment (most finalized to least finalized), clients may specify:
"""
from typing import NewType

Commitment = NewType("Commitment", str)
"""Type for commitment."""

Max = Commitment("max")
"""The node will query the most recent bank confirmed by the cluster as having
reached `MAX_LOCKOUT_HISTORY` confirmations."""

Root = Commitment("root")
"""The node will query the most recent bank having reached `MAX_LOCKOUT_HISTORY` confirmations on this node."""

Single = Commitment("singleGossip")
"""The node will query the most recent block that has been voted on by supermajority of the cluster.

- It incorporates votes from gossip and replay.
- It does not count votes on descendants of a block, only direct votes on that block.
- This confirmation level also upholds "optimistic confirmation" guarantees in release 1.3 and onwards.
"""

Recent = Commitment("recent")
"""The node will query its most recent bank."""
