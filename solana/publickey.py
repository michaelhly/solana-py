"""Library to interface with Solana public keys."""
from __future__ import annotations

from hashlib import sha256
from typing import Any, List, Optional, Tuple, Union

import base58

from solana.utils import ed25519_base, helpers


class PublicKey:
    """The public key of a keypair.

    >>> # An arbitary public key:
    >>> pubkey = PublicKey(1)
    >>> str(pubkey) # String representation in base58 form.
    '11111111111111111111111111111112'
    >>> bytes(pubkey).hex()
    '0000000000000000000000000000000000000000000000000000000000000001'
    """

    LENGTH = 32
    """Constant for standard length of a public key."""

    def __init__(self, value: Union[bytearray, bytes, int, str, List[int]]) -> None:
        """Init PublicKey object."""
        self._key: Optional[bytes] = None
        if isinstance(value, str):
            try:
                self._key = base58.b58decode(value)
            except ValueError as err:
                raise ValueError("invalid public key input:", value) from err
            if len(self._key) != self.LENGTH:
                raise ValueError("invalid public key input:", value)
        elif isinstance(value, int):
            self._key = bytes([value])
        else:
            self._key = bytes(value)

        if len(self._key) > self.LENGTH:
            raise ValueError("invalid public key input:", value)

    def __bytes__(self) -> bytes:
        """Public key in bytes."""
        if not self._key:
            return bytes(self.LENGTH)
        return self._key if len(self._key) == self.LENGTH else self._key.rjust(self.LENGTH, b"\0")

    def __eq__(self, other: Any) -> bool:
        """Equality definition for PublicKeys."""
        return False if not isinstance(other, PublicKey) else bytes(self) == bytes(other)

    def __repr__(self) -> str:
        """Representation of a PublicKey."""
        return str(self)

    def __str__(self) -> str:
        """String definition for PublicKey."""
        return self.to_base58().decode("utf-8")

    def to_base58(self) -> bytes:
        """Public key in base58."""
        return base58.b58encode(bytes(self))

    @staticmethod
    def create_with_seed(from_public_key: PublicKey, seed: str, program_id: PublicKey) -> PublicKey:
        """Derive a public key from another key, a seed, and a program ID."""
        buf = bytes(from_public_key) + seed.encode("utf-8") + bytes(program_id)
        return PublicKey(sha256(buf).digest())

    @staticmethod
    def create_program_address(seeds: List[bytes], program_id: PublicKey) -> PublicKey:
        """Derive a program address from seeds and a program ID."""
        buffer = b"".join(seeds + [bytes(program_id), b"ProgramDerivedAddress"])
        hashbytes: bytes = sha256(buffer).digest()
        if not PublicKey._is_on_curve(hashbytes):
            return PublicKey(hashbytes)
        raise Exception("Invalid seeds, address must fall off the curve")

    @staticmethod
    def find_program_address(seeds: List[bytes], program_id: PublicKey) -> Tuple[PublicKey, int]:
        """Find a valid program address.

        Valid program addresses must fall off the ed25519 curve.  This function
        iterates a nonce until it finds one that when combined with the seeds
        results in a valid program address.
        """
        nonce = 255
        while nonce != 0:
            try:
                buffer = seeds + [helpers.to_uint8_bytes(nonce)]
                address = PublicKey.create_program_address(buffer, program_id)
            except Exception:
                nonce -= 1
                continue
            return address, nonce
        raise KeyError("Unable to find a viable program address nonce")

    @staticmethod
    def _is_on_curve(pubkey_bytes: bytes) -> bool:
        """Verify the point is on curve or not."""
        return ed25519_base.is_on_curve(pubkey_bytes)
