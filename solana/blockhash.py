"""Blockhash.

>>> # An arbitrary base58 encoded blockhash:
>>> Blockhash("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k")
'EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k'
"""
from typing import NewType

Blockhash = NewType("Blockhash", str)
"""Type for blockhash."""
