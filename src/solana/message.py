"""Library for generating a message from a sequence of instructions."""
from __future__ import annotations

from typing import List, NamedTuple, Union

from base58 import b58decode, b58encode

from solana.blockhash import Blockhash
from solana.publickey import PublicKey
from solana.utils import helpers
from solana.utils import shortvec_encoding as shortvec


class CompiledInstruction(NamedTuple):
    """An instruction to execute by a program."""

    accounts: Union[bytes, List[int]]
    """Ordered indices into the transaction keys array indicating which accounts to pass to the program."""
    program_id_index: int
    """Index into the transaction keys array indicating the program account that executes this instruction."""
    data: bytes
    """The program input data encoded as base 58."""


class MessageHeader(NamedTuple):
    """The message header, identifying signed and read-only account."""

    num_required_signatures: int
    """The number of signatures required for this message to be considered valid."""
    num_readonly_signed_accounts: int
    """The last `numReadonlySignedAccounts` of the signed keys are read-only accounts."""
    num_readonly_unsigned_accounts: int
    """The last `numReadonlySignedAccounts` of the unsigned keys are read-only accounts."""


class MessageArgs(NamedTuple):
    """Message constructor arguments."""

    header: MessageHeader
    """The message header, identifying signed and read-only `accountKeys`."""
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
        self.header = args.header
        self.account_keys = [PublicKey(key) for key in args.account_keys]
        self.recent_blockhash = args.recent_blockhash
        self.instructions = args.instructions

    def __encode_message(self) -> bytes:  # TODO: Replace this with a construct struct.
        MessageFormat = NamedTuple(
            "MessageFormat",
            [
                ("num_required_signatures", bytes),
                ("num_readonly_signed_accounts", bytes),
                ("num_readonly_unsigned_accounts", bytes),
                ("pubkeys_length", bytes),
                ("pubkeys", bytes),
                ("recent_blockhash", bytes),
            ],
        )
        return b"".join(
            MessageFormat(
                num_required_signatures=helpers.to_uint8_bytes(self.header.num_required_signatures),
                num_readonly_signed_accounts=helpers.to_uint8_bytes(self.header.num_readonly_signed_accounts),
                num_readonly_unsigned_accounts=helpers.to_uint8_bytes(self.header.num_readonly_unsigned_accounts),
                pubkeys_length=shortvec.encode_length(len(self.account_keys)),
                pubkeys=b"".join([bytes(pubkey) for pubkey in self.account_keys]),
                recent_blockhash=b58decode(self.recent_blockhash),
            )
        )

    @staticmethod
    def __encode_instruction(
        instruction: "CompiledInstruction",
    ) -> bytes:  # TODO: Replace this with a construct struct.
        InstructionFormat = NamedTuple(
            "InstructionFormat",
            [
                ("program_idx", bytes),
                ("accounts_length", bytes),
                ("accounts", bytes),
                ("data_length", bytes),
                ("data", bytes),
            ],
        )
        data = b58decode(instruction.data)
        data_length = shortvec.encode_length(len(data))
        return b"".join(
            InstructionFormat(
                program_idx=helpers.to_uint8_bytes(instruction.program_id_index),
                accounts_length=shortvec.encode_length(len(instruction.accounts)),
                accounts=bytes(instruction.accounts),
                data_length=data_length,
                data=data,
            )
        )

    def is_account_writable(self, index: int) -> bool:
        """Check if account is write eligble."""
        writable = index < (self.header.num_required_signatures - self.header.num_readonly_signed_accounts)
        return writable or self.header.num_required_signatures <= index < (
            len(self.account_keys) - self.header.num_readonly_unsigned_accounts
        )

    def serialize(self) -> bytes:
        """Serialize message to bytes.

        >>> from solana.blockhash import Blockhash
        >>> account_keys = [str(PublicKey(i + 1)) for i in range(5)]
        >>> msg = Message(
        ...     MessageArgs(
        ...         account_keys=account_keys,
        ...         header=MessageHeader(
        ...             num_readonly_signed_accounts=0, num_readonly_unsigned_accounts=3, num_required_signatures=2
        ...         ),
        ...         instructions=[
        ...             CompiledInstruction(accounts=[1, 2, 3], data=b58encode(bytes([9] * 5)), program_id_index=4)],
        ...         recent_blockhash=Blockhash("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k"),
        ...     )
        ... )
        >>> msg.serialize().hex()
        '0200030500000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000005c49ae77603782054f17a9decea43b444eba0edb12c6f1d31c6e0e4a84bf052eb010403010203050909090909'
        """  # pylint: disable=line-too-long
        message_buffer = bytearray()
        # Message body
        message_buffer.extend(self.__encode_message())
        # Instructions
        instruction_count = shortvec.encode_length(len(self.instructions))
        message_buffer.extend(instruction_count)
        for instr in self.instructions:
            message_buffer.extend(Message.__encode_instruction(instr))
        return bytes(message_buffer)

    @staticmethod
    def deserialize(raw_message: bytes) -> Message:
        """Deserialize raw message bytes.

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
        """
        HEADER_OFFSET = 3  # pylint: disable=invalid-name
        if len(raw_message) < HEADER_OFFSET:
            raise ValueError("byte representation of message is missing message header")
        num_required_signatures = raw_message[0]
        num_readonly_signed_accounts = raw_message[1]
        num_readonly_unsigned_accounts = raw_message[2]
        header = MessageHeader(
            num_required_signatures=num_required_signatures,
            num_readonly_signed_accounts=num_readonly_signed_accounts,
            num_readonly_unsigned_accounts=num_readonly_unsigned_accounts,
        )
        raw_message = raw_message[HEADER_OFFSET:]

        account_keys = []
        accounts_length, accounts_offset = shortvec.decode_length(raw_message)
        for _ in range(accounts_length):
            key_bytes = raw_message[accounts_offset : accounts_offset + PublicKey.LENGTH]  # noqa: E203
            account_keys.append(str(PublicKey(key_bytes)))
            accounts_offset += PublicKey.LENGTH
        raw_message = raw_message[accounts_offset:]

        recent_blockhash = Blockhash(b58encode(raw_message[: PublicKey.LENGTH]).decode("utf-8"))
        raw_message = raw_message[PublicKey.LENGTH :]  # noqa: E203

        instructions = []
        instruction_count, offset = shortvec.decode_length(raw_message)
        raw_message = raw_message[offset:]
        for _ in range(instruction_count):
            program_id_index = raw_message[0]
            raw_message = raw_message[1:]

            accounts_length, offset = shortvec.decode_length(raw_message)
            raw_message = raw_message[offset:]
            accounts = raw_message[:accounts_length]
            raw_message = raw_message[accounts_length:]

            data_length, offset = shortvec.decode_length(raw_message)
            raw_message = raw_message[offset:]
            data = b58encode(raw_message[:data_length])
            raw_message = raw_message[data_length:]

            instructions.append(CompiledInstruction(program_id_index=program_id_index, accounts=accounts, data=data))

        return Message(
            MessageArgs(
                header=header,
                account_keys=account_keys,
                recent_blockhash=recent_blockhash,
                instructions=instructions,
            )
        )
