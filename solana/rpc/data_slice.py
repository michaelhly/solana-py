"""DataSlice options.

limit the returned account data using the provided offset: <usize> and
length: <usize> fields; only available for "base58" or "base64" encoding.
"""
from dataclasses import dataclass


@dataclass
class DataSlice:
    offset: int
    length: int
