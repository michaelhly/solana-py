"""Commitment options.

Solana nodes choose which bank state to query based on a commitment requirement set by the client.
Clients may specify the following commitments:
"""
from typing import NewType

Commitment = NewType("Commitment", str)
"""Type for commitment."""

Max = Commitment("max")
"""The node will query the most recent bank confirmed by the cluster as having
reached `MAX_LOCKOUT_HISTORY` confirmations."""

Root = Commitment("root")
"""The node will query the most recent bank having reached `MAX_LOCKOUT_HISTORY` confirmations on this node."""

Single = Commitment("single")
"""The node will query the most recent bank having reached 1 confirmation."""

Recent = Commitment("recent")
"""The node will query its most recent bank."""
