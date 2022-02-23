"""Keypair module to manage public-private key pair."""
from __future__ import annotations

from typing import Optional

import nacl.public  # type: ignore
from nacl import signing  # type: ignore

import solana.publickey


class Keypair:
    """An account keypair used for signing transactions.

    Args:
        keypair: an `nacl.public.PrivateKey` instance.

    Example:
        >>> # Init with random keypair:
        >>> keypair = Keypair()
        >>> # Init with existing keypair:
        >>> keys = nacl.public.PrivateKey.generate()
        >>> keypair = Keypair(keys)
    """

    def __init__(self, keypair: Optional[nacl.public.PrivateKey] = None) -> None:
        """Create a new keypair instance.

        Generate random keypair if no keypair is provided. Initialize class variables.
        """
        if keypair is None:
            # the PrivateKey object comes with a public key too
            self._keypair = nacl.public.PrivateKey.generate()
        else:
            self._keypair = keypair

        verify_key = signing.SigningKey(bytes(self._keypair)).verify_key

        self._public_key = solana.publickey.PublicKey(verify_key)

    @classmethod
    def generate(cls) -> Keypair:
        """Generate a new random keypair.

        This method exists to provide familiarity for web3.js users.
        There isn't much reason to use it instead of just instantiating
        `Keypair()`.

        Returns:
            The generated keypair.
        """
        return cls()

    @classmethod
    def from_secret_key(cls, secret_key: bytes) -> Keypair:
        """Create a keypair from the 64-byte secret key.

        This method should only be used to recreate a keypair from a previously
        generated secret key. Generating keypairs from a random seed should be done
        with the `.from_seed` method.

        Args:

            secret_key: secret key in bytes.

        Returns:
            The generated keypair.
        """
        seed = secret_key[:32]
        return cls.from_seed(seed)

    @classmethod
    def from_seed(cls, seed: bytes) -> Keypair:
        """Generate a keypair from a 32 byte seed.

        Args:

            seed: 32-byte seed.

        Returns:
            The generated keypair.
        """
        return cls(nacl.public.PrivateKey(seed))

    def sign(self, msg: bytes) -> signing.SignedMessage:
        """Sign a message with this keypair.

        Args:

            msg: message to sign.

        Returns:
            A signed messeged object.

        Example:

            >>> seed = bytes([1] * 32)
            >>> keypair = Keypair.from_seed(seed)
            >>> msg = b"hello"
            >>> signed_msg = keypair.sign(msg)
            >>> signed_msg.signature.hex()
            'e1430c6ebd0d53573b5c803452174f8991ef5955e0906a09e8fdc7310459e9c82a402526748c3431fe7f0e5faafbf7e703234789734063ee42be17af16438d08'
            >>> signed_msg.message.decode('utf-8')
            'hello'
        """  # pylint: disable=line-too-long
        return signing.SigningKey(self.seed).sign(msg)

    @property
    def seed(self) -> bytes:
        """The 32-byte secret seed."""
        return bytes(self._keypair)

    @property
    def public_key(self) -> solana.publickey.PublicKey:
        """The public key for this keypair."""
        return self._public_key

    @property
    def secret_key(self) -> bytes:
        """The raw 64-byte secret key for this keypair."""
        return self.seed + bytes(self.public_key)

    def __eq__(self, other) -> bool:
        """Checks for equality by comparing public keys."""
        if not isinstance(other, self.__class__):
            return False
        return self.secret_key == other.secret_key

    def __ne__(self, other) -> bool:
        """Implemented by negating __eq__."""
        return not (self == other)  # pylint: disable=superfluous-parens

    def __hash__(self) -> int:
        """Returns a unique hash for set operations."""
        return hash(self._keypair)
