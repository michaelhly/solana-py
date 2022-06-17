"""Library for generating a message from a sequence of instructions."""
from __future__ import annotations

from typing import List, NamedTuple

from solders.hash import Hash
from solders.instruction import CompiledInstruction
from solders.message import Message as SoldersMessage
from solders.message import MessageHeader
from solders.pubkey import Pubkey

from solana.blockhash import Blockhash
from solana.publickey import PublicKey


class MessageArgs(NamedTuple):
    """Message constructor arguments."""

    header: MessageHeader
    """The message header, identifying signed and read-only `account_keys`."""
    account_keys: List[str]
    """All the account keys used by this transaction."""
    recent_blockhash: Blockhash
    """The hash of a recent ledger block."""
    instructions: List[CompiledInstruction]
    """Instructions that will be executed in sequence and committed in one atomic transaction if all succeed."""


class Message:
    """Message object to be used to to build a transaction.

    A message contains a header, followed by a compact-array of account addresses, followed by a recent blockhash,
    followed by a compact-array of instructions.
    """

    def __init__(self, args: MessageArgs) -> None:
        """Init message object."""
        header = args.header
        blockhash = Hash.from_string(args.recent_blockhash)
        account_keys = [Pubkey.from_string(key) for key in args.account_keys]
        self._solders = SoldersMessage.new_with_compiled_instructions(
            num_required_signatures=header.num_required_signatures,
            num_readonly_signed_accounts=header.num_readonly_signed_accounts,
            num_readonly_unsigned_accounts=header.num_readonly_unsigned_accounts,
            account_keys=account_keys,
            recent_blockhash=blockhash,
            instructions=args.instructions,
        )

    @classmethod
    def from_solders(cls, msg: SoldersMessage) -> Message:
        """Convert from a `solders` message.

        Args:
            msg: The `solders` message.

        Returns:
            A `solana-py` message.
        """
        args = MessageArgs(
            header=msg.header,
            account_keys=[str(key) for key in msg.account_keys],
            recent_blockhash=Blockhash(str(msg.recent_blockhash)),
            instructions=msg.instructions,
        )
        return cls(args)

    def to_solders(self) -> SoldersMessage:
        """Convert to a `solders` message.

        Returns:
            A `solders` message.
        """
        return self._solders

    @property
    def header(self) -> MessageHeader:
        """Get the message header, identifying signed and read-only `account_keys`.

        Returns:
            The message header.
        """
        return self._solders.header

    @property
    def account_keys(self) -> List[PublicKey]:
        """All the account keys used by this transaction.

        Returns:
            The account keys.
        """
        return [PublicKey.from_solders(pubkey) for pubkey in self._solders.account_keys]

    @property
    def recent_blockhash(self) -> Blockhash:
        """The hash of a recent ledger block.

        Returns:
            The blockhash.
        """
        return Blockhash(str(self._solders.recent_blockhash))

    @property
    def instructions(self) -> List[CompiledInstruction]:
        """Instructions that will be executed in sequence and committed in one atomic transaction if all succeed.

        Returns:
            The message instructions.
        """
        return self._solders.instructions

    def is_account_writable(self, index: int) -> bool:
        """Check if account is write eligble."""
        return self._solders.is_writable(index)

    def serialize(self) -> bytes:
        """Serialize message to bytes.

        Example:

            >>> from solana.blockhash import Blockhash
            >>> account_keys = [str(PublicKey(i + 1)) for i in range(5)]
            >>> msg = Message(
            ...     MessageArgs(
            ...         account_keys=account_keys,
            ...         header=MessageHeader(
            ...             num_readonly_signed_accounts=0, num_readonly_unsigned_accounts=3, num_required_signatures=2
            ...         ),
            ...         instructions=[
            ...             CompiledInstruction(accounts=bytes([1, 2, 3]), data=bytes([9] * 5), program_id_index=4)],
            ...         recent_blockhash=Blockhash("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k"),
            ...     )
            ... )
            >>> msg.serialize().hex()
            '0200030500000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000005c49ae77603782054f17a9decea43b444eba0edb12c6f1d31c6e0e4a84bf052eb010403010203050909090909'

        Returns:
            The serialized message.
        """  # pylint: disable=line-too-long # noqa: E501
        return bytes(self._solders)

    @classmethod
    def deserialize(cls, raw_message: bytes) -> Message:  # pylint: disable=too-many-locals
        """Deserialize raw message bytes.

        Example:

            >>> raw_message = bytes.fromhex(
            ...     '0200030500000000000000000000000000000000000000000000'
            ...     '0000000000000000000100000000000000000000000000000000'
            ...     '0000000000000000000000000000000200000000000000000000'
            ...     '0000000000000000000000000000000000000000000300000000'
            ...     '0000000000000000000000000000000000000000000000000000'
            ...     '0004000000000000000000000000000000000000000000000000'
            ...     '0000000000000005c49ae77603782054f17a9decea43b444eba0'
            ...     'edb12c6f1d31c6e0e4a84bf052eb010403010203050909090909'
            ... )
            >>> type(Message.deserialize(raw_message))
            <class 'solana.message.Message'>

        Returns:
            The deserialized message.
        """
        msg = SoldersMessage.from_bytes(raw_message)
        return cls.from_solders(msg)
