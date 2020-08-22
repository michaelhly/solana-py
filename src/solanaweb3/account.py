"""Account class to manage public-private key pair and signing messages."""
from __future__ import annotations
from typing import List, Optional, Union

from nacl import public, signing  # type: ignore

from solanaweb3.publickey import PublicKey


class Account:
    """An account key pair (public and secret keys)."""

    def __init__(self, secret_key: Optional[Union[bytes, str, List[int]]] = None):
        key: Optional[bytes] = None
        if isinstance(secret_key, list):
            key = bytes(secret_key)
        elif isinstance(secret_key, str):
            key = bytes(secret_key, encoding="utf-8")
        elif isinstance(secret_key, bytes):
            key = secret_key

        self._secret = public.PrivateKey(key) if key else public.PrivateKey.generate()

    def public_key(self) -> PublicKey:
        """The public key for this account."""
        return PublicKey(bytes(self._secret.public_key))

    def secret_key(self) -> bytes:
        """The **unencrypted** secret key for this account."""
        return bytes(self._secret)

    def sign(self, msg: bytes) -> bytes:
        """Sign a message with the account."""
        return signing.SigningKey(self.secret_key).sign(msg)
