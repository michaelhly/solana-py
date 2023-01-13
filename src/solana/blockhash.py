"""Blockhash utils."""

from cachetools import TTLCache
from solders.hash import Hash


class BlockhashCache:
    """A recent blockhash cache that expires after a given number of seconds.

    Args:
        ttl: Seconds until cached blockhash expires.
    """

    def __init__(self, ttl: int = 60) -> None:
        """Instantiate the cache (you only need to do this once)."""
        maxsize = 300
        self.unused_blockhashes: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.used_blockhashes: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)

    def set(self, blockhash: Hash, slot: int, used_immediately: bool = False) -> None:
        """Update the cache.

        Args:
            blockhash: new blockhash value.
            slot: the slot which the blockhash came from.
            used_immediately: whether the client used the blockhash immediately after fetching it.

        """
        if used_immediately:
            if slot not in self.used_blockhashes:
                self.used_blockhashes[slot] = blockhash
            return
        if slot in self.used_blockhashes or slot in self.unused_blockhashes:
            return
        self.unused_blockhashes[slot] = blockhash

    def get(self) -> Hash:
        """Get the cached blockhash. Raises KeyError if cache has expired.

        Returns:
            cached blockhash.

        """
        try:
            slot, blockhash = self.unused_blockhashes.popitem()
            self.used_blockhashes[slot] = blockhash
        except KeyError:
            with self.used_blockhashes.timer:  # type: ignore
                blockhash = self.used_blockhashes[min(self.used_blockhashes)]
                # raises ValueError if used_blockhashes is empty
        return blockhash
