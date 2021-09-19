"""Blockhash.

>>> # An arbitrary base58 encoded blockhash:
>>> Blockhash("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k")
'EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k'
"""
from typing import NewType
from cachetools import TTLCache

Blockhash = NewType("Blockhash", str)
"""Type for blockhash."""


class BlockhashCache:
    """A recent blockhash cache that expires after a given number of seconds."""

    def __init__(self, ttl: int = 60) -> None:
        """Instantiate the cache (you only need to do this once).

        Args:
        ----
            ttl (int): Seconds until cached blockhash expires.

        """
        maxsize = 300
        self.unused_blockhashes: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.used_blockhashes: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)

    def set(self, blockhash: Blockhash, slot: int) -> None:
        """Update the cache.

        Args:
        ----
            blockhash (Blockhash): new Blockhash value.
            slot (int): the slot which the blockhash came from

        """
        if slot in self.used_blockhashes or slot in self.unused_blockhashes:
            return
        self.unused_blockhashes[slot] = blockhash

    def get(self) -> Blockhash:
        """Get the cached Blockhash. Raises KeyError if cache has expired.

        Returns
        -------
            Blockhash: cached Blockhash.

        """
        try:
            slot, blockhash = self.unused_blockhashes.popitem()
            self.used_blockhashes[slot] = blockhash
        except KeyError:
            with self.used_blockhashes.timer:  # type: ignore
                blockhash = self.used_blockhashes[min(self.used_blockhashes)]
                # raises ValueError if used_blockhashes is empty
        return blockhash
