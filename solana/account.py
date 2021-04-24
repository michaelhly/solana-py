"""Account module to manage public-private key pair and signing messages."""
from __future__ import annotations

from typing import List, Optional, Union

from base58 import b58encode
from nacl import public, signing  # type: ignore

from solana.publickey import PublicKey


class Account:
    """An account key pair (public and secret keys).

    >>> # Import account from 64-byte keypair
    >>> keypair = [
    ...     90, 249, 112, 214, 86, 235, 20, 215, 175, 33, 227, 50, 72, 214, 59, 49,
    ...     38, 161, 99, 83, 107, 188, 57, 48, 119, 189, 46, 148, 160, 214, 239, 148,
    ...     219, 250, 20, 106, 35, 41, 118, 107, 89, 96, 195, 15, 153, 248, 223, 6,
    ...     46, 71, 142, 92, 169, 240, 177, 106, 86, 194, 21, 62, 29, 222, 206, 82]
    >>> account = Account(keypair[:32])
    >>> account.public_key()
    4HtxMbEK1QYzo9KjXEZoDeGrkhYkDtWdiQUARxz5VCoW
    """

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
        """The public key for this account."""
        verify_key = signing.SigningKey(self.secret_key()).verify_key
        return PublicKey(bytes(verify_key))

    def secret_key(self) -> bytes:
        """The **Unencrypted** secret key for this account."""
        return bytes(self._secret)

    def keypair(self) -> bytes:
        """The 64 byte keypair for this account (base 58 encoded)."""
        return b58encode(self.secret_key() + bytes(signing.SigningKey(self.secret_key()).verify_key))

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
