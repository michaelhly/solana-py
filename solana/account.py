"""Account module to manage public-private key pair and signing messages."""
from __future__ import annotations

from typing import List, Optional, Union

from nacl import public, signing  # type: ignore

from solana.publickey import PublicKey


class Account:
    """An account key pair (public and secret keys)."""

    def __init__(self, secret_key: Optional[Union[bytes, str, List[int], int]] = None):
        """Create a new Account object.

        :pararm secret_key: Secret key for the account.
        """
        key: Optional[bytes] = None
        if isinstance(secret_key, int):
            key = bytes(PublicKey(secret_key))
        if isinstance(secret_key, list):
            key = bytes(secret_key)
        elif isinstance(secret_key, str):
            key = bytes(secret_key, encoding="utf-8")
        elif isinstance(secret_key, bytes):
            key = secret_key

        self._secret = public.PrivateKey(key) if key else public.PrivateKey.generate()

    def public_key(self) -> PublicKey:
        """The Public key for this account."""
        verify_key = signing.SigningKey(self.secret_key()).verify_key
        return PublicKey(bytes(verify_key))

    def secret_key(self) -> bytes:
        """The **Unencrypted** secret key for this account."""
        return bytes(self._secret)

    def sign(self, msg: bytes) -> signing.SignedMessage:
        """Sign a message with this account.

        :param msg: message to sign.
        :returns: A signed messeged object.

        >>> secret_key = bytes([1] * 32)
        >>> acc = Account(secret_key)
        >>> msg = b"hello"
        >>> signed_msg = acc.sign(msg)
        >>> signed_msg.signature.hex()
        'e1430c6ebd0d53573b5c803452174f8991ef5955e0906a09e8fdc7310459e9c82a402526748c3431fe7f0e5faafbf7e703234789734063ee42be17af16438d08'
        >>> signed_msg.message.decode('utf-8')
        'hello'
        """  # pylint: disable=line-too-long
        return signing.SigningKey(self.secret_key()).sign(msg)
