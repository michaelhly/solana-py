"""Library to package an atomic sequence of instructions to a transaction."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, NamedTuple, NewType, Optional, Sequence, Tuple, Union

from solders import instruction
from solders.hash import Hash
from solders.instruction import AccountMeta as SoldersAccountMeta
from solders.instruction import Instruction
from solders.message import Message as SoldersMessage
from solders.presigner import Presigner
from solders.signature import Signature
from solders.transaction import Transaction as SoldersTx
from solders.transaction import TransactionError

from solana.blockhash import Blockhash
from solana.keypair import Keypair
from solana.message import Message
from solana.publickey import PublicKey

TransactionSignature = NewType("TransactionSignature", str)
"""Type for TransactionSignature."""
PACKET_DATA_SIZE = 1280 - 40 - 8
"""Constant for maximum over-the-wire size of a Transaction."""
SIG_LENGTH = 64
"""Constant for standard length of a signature."""


@dataclass
class AccountMeta:
    """Account metadata dataclass."""

    pubkey: PublicKey
    """An account's public key."""
    is_signer: bool
    """True if an instruction requires a transaction signature matching `pubkey`"""
    is_writable: bool
    """True if the `pubkey` can be loaded as a read-write account."""

    @classmethod
    def from_solders(cls, meta: instruction.AccountMeta) -> AccountMeta:
        """Convert from a `solders` AccountMeta.

        Args:
            meta: The `solders` AccountMeta.

        Returns:
            The `solana-py` AccountMeta.
        """
        return cls(pubkey=PublicKey.from_solders(meta.pubkey), is_signer=meta.is_signer, is_writable=meta.is_writable)

    def to_solders(self) -> instruction.AccountMeta:
        """Convert to a `solders` AccountMeta.

        Returns:
            The `solders` AccountMeta.
        """
        return instruction.AccountMeta(
            pubkey=self.pubkey.to_solders(), is_signer=self.is_signer, is_writable=self.is_writable
        )


class TransactionInstruction(NamedTuple):
    """Transaction Instruction class."""

    keys: List[AccountMeta]
    """Public keys to include in this transaction Boolean represents whether this
    pubkey needs to sign the transaction.
    """
    program_id: PublicKey
    """Program Id to execute."""
    data: bytes = bytes(0)
    """Program input."""

    @classmethod
    def from_solders(cls, ixn: instruction.Instruction) -> TransactionInstruction:
        """Convert from a `solders` instruction.

        Args:
            ixn: The `solders` instruction.

        Returns:
            The `solana-py` instruction.
        """
        keys = [AccountMeta.from_solders(am) for am in ixn.accounts]
        program_id = PublicKey.from_solders(ixn.program_id)
        return cls(keys=keys, program_id=program_id, data=ixn.data)

    def to_solders(self) -> instruction.Instruction:
        """Convert to a `solders` instruction.

        Returns:
            The `solders` instruction.
        """
        accounts = [key.to_solders() for key in self.keys]
        return instruction.Instruction(program_id=self.program_id.to_solders(), data=self.data, accounts=accounts)


class NonceInformation(NamedTuple):
    """NonceInformation to be used to build a Transaction."""

    nonce: Blockhash
    """The current Nonce blockhash."""
    nonce_instruction: TransactionInstruction
    """AdvanceNonceAccount Instruction."""


@dataclass
class SigPubkeyPair:
    """Pair of signature and corresponding public key."""

    pubkey: PublicKey
    signature: Optional[bytes] = None


def _build_solders_tx(
    recent_blockhash: Optional[Blockhash] = None,
    nonce_info: Optional[NonceInformation] = None,
    fee_payer: Optional[PublicKey] = None,
    instructions: Optional[Sequence[TransactionInstruction]] = None,
) -> SoldersTx:
    core_instructions = [] if instructions is None else [ixn.to_solders() for ixn in instructions]
    underlying_instructions = (
        core_instructions if nonce_info is None else [nonce_info.nonce_instruction.to_solders(), *core_instructions]
    )
    underlying_blockhash_str: Optional[str]
    if nonce_info is not None:
        underlying_blockhash_str = nonce_info.nonce
    elif recent_blockhash is not None:
        underlying_blockhash_str = recent_blockhash
    else:
        underlying_blockhash_str = None
    underlying_fee_payer = None if fee_payer is None else fee_payer.to_solders()
    underlying_blockhash = (
        Hash.default() if underlying_blockhash_str is None else Hash.from_string(underlying_blockhash_str)
    )
    msg = SoldersMessage.new_with_blockhash(underlying_instructions, underlying_fee_payer, underlying_blockhash)
    return SoldersTx.new_unsigned(msg)


def _decompile_instructions(msg: SoldersMessage) -> List[TransactionInstruction]:
    account_keys = msg.account_keys
    decompiled_instructions: List[Instruction] = []
    for compiled_ix in msg.instructions:
        program_id = account_keys[compiled_ix.program_id_index]
        account_metas = [
            SoldersAccountMeta(account_keys[idx], is_signer=msg.is_signer(idx), is_writable=msg.is_writable(idx))
            for idx in compiled_ix.accounts
        ]
        decompiled_instructions.append(Instruction(program_id, compiled_ix.data, account_metas))
    return [TransactionInstruction.from_solders(ixn) for ixn in decompiled_instructions]


class Transaction:
    """Transaction class to represent an atomic transaction.

    Args:
        recent_blockhash: A recent transaction id.
        nonce_info: Nonce information.
            If populated, transaction will use a durable Nonce hash instead of a `recent_blockhash`.
        fee_payer: The transaction fee payer.
        instructions: The instructions to be executed in this transaction.
    """

    # Default (empty) signature
    __DEFAULT_SIG = bytes(64)

    def __init__(
        self,
        recent_blockhash: Optional[Blockhash] = None,
        nonce_info: Optional[NonceInformation] = None,
        fee_payer: Optional[PublicKey] = None,
        instructions: Optional[Sequence[TransactionInstruction]] = None,
    ) -> None:
        """Init transaction object."""
        self._solders = _build_solders_tx(
            recent_blockhash=recent_blockhash, nonce_info=nonce_info, fee_payer=fee_payer, instructions=instructions
        )

    @classmethod
    def from_solders(cls, txn: SoldersTx) -> Transaction:
        """Convert from a `solders` transaction.

        Args:
            txn: The `solders` transaction.

        Returns:
            The `solana-py` transaction.
        """
        new_tx = cls()
        new_tx._solders = txn
        return new_tx

    def to_solders(self) -> SoldersTx:
        """Convert to a `solders` transaction.

        Returns:
            The `solders` transaction.
        """
        return self._solders

    def __eq__(self, other: Any) -> bool:
        """Equality defintion for Transactions."""
        if not isinstance(other, Transaction):
            return False
        return self.to_solders() == other.to_solders()

    @property
    def recent_blockhash(self) -> Optional[Blockhash]:
        """Optional[Blockhash]: The blockhash assigned to this transaction."""
        return Blockhash(str(self._solders.message.recent_blockhash))

    @recent_blockhash.setter
    def recent_blockhash(self, blockhash: Optional[Blockhash]) -> None:
        self._solders = _build_solders_tx(
            recent_blockhash=blockhash, nonce_info=None, fee_payer=self.fee_payer, instructions=self.instructions
        )

    @property
    def fee_payer(self) -> Optional[PublicKey]:
        """Optional[PublicKey]: The transaction fee payer."""
        account_keys = self._solders.message.account_keys
        return PublicKey.from_solders(account_keys[0]) if account_keys else None

    @fee_payer.setter
    def fee_payer(self, payer: Optional[PublicKey]) -> None:
        self._solders = _build_solders_tx(
            recent_blockhash=self.recent_blockhash, nonce_info=None, fee_payer=payer, instructions=self.instructions
        )

    @property
    def instructions(self) -> Tuple[TransactionInstruction, ...]:
        """Tuple[TransactionInstruction]: The instructions contained in this transaction."""
        msg = self._solders.message
        return tuple(_decompile_instructions(msg))

    @instructions.setter
    def instructions(self, ixns: Sequence[TransactionInstruction]) -> None:
        self._solders = _build_solders_tx(
            recent_blockhash=self.recent_blockhash, nonce_info=None, fee_payer=self.fee_payer, instructions=ixns
        )

    @property
    def signatures(self) -> Tuple[Signature, ...]:
        """Tuple[Signature]: Signatures for the transaction."""
        return tuple(self._solders.signatures)

    def signature(self) -> Signature:
        """The first (payer) Transaction signature.

        Returns:
            The payer signature.
        """
        return self._solders.signatures[0]

    def add(self, *args: Union[Transaction, TransactionInstruction]) -> Transaction:
        """Add one or more instructions to this Transaction.

        Args:
            *args: The instructions to add to this Transaction.
                If a `Transaction` is passsed, the instructions will be extracted from it.

        Returns:
            The transaction with the added instructions.
        """
        for arg in args:
            if isinstance(arg, Transaction):
                self.instructions = self.instructions + arg.instructions
            elif isinstance(arg, TransactionInstruction):
                self.instructions = (*self.instructions, arg)
            else:
                raise ValueError("invalid instruction:", arg)

        return self

    def compile_message(self) -> Message:  # pylint: disable=too-many-locals
        """Compile transaction data.

        Returns:
            The compiled message.
        """
        return Message.from_solders(self._solders.message)

    def serialize_message(self) -> bytes:
        """Get raw transaction data that need to be covered by signatures.

        Returns:
            The serialized message.
        """
        return self.compile_message().serialize()

    def sign_partial(self, *partial_signers: Keypair) -> None:
        """Partially sign a Transaction with the specified keypairs.

        All the caveats from the `sign` method apply to `sign_partial`
        """
        underlying_signers = [signer.to_solders() for signer in partial_signers]
        self._solders.partial_sign(underlying_signers, self._solders.message.recent_blockhash)

    def sign(self, *signers: Keypair) -> None:
        """Sign the Transaction with the specified accounts.

        Multiple signatures may be applied to a Transaction. The first signature
        is considered "primary" and is used when testing for Transaction confirmation.

        Transaction fields should not be modified after the first call to `sign`,
        as doing so may invalidate the signature and cause the Transaction to be
        rejected.

        The Transaction must be assigned a valid `recent_blockhash` before invoking this method.
        """
        underlying_signers = [signer.to_solders() for signer in signers]
        self._solders.sign(underlying_signers, self._solders.message.recent_blockhash)

    def add_signature(self, pubkey: PublicKey, signature: Signature) -> None:
        """Add an externally created signature to a transaction.

        Args:
            pubkey: The public key that created the signature.
            signature: The signature to add.
        """
        presigner = Presigner(pubkey.to_solders(), signature)
        self._solders.partial_sign([presigner], self._solders.message.recent_blockhash)

    def verify_signatures(self) -> bool:
        """Verify signatures of a complete, signed Transaction.

        Returns:
            a bool indicating if the signatures are correct or not.
        """
        try:
            self._solders.verify()
        except TransactionError:
            return False
        return True

    def serialize(self, verify_signatures: bool = True) -> bytes:
        """Serialize the Transaction in the wire format.

        The Transaction must have a valid `signature` before invoking this method.
        verify_signatures can be added if the signature does not require to be verified.

        Args:
            verify_signatures: a bool indicating to verify the signature or not. Defaults to True

        Example:

            >>> from solana.keypair import Keypair
            >>> from solana.blockhash import Blockhash
            >>> from solana.publickey import PublicKey
            >>> from solana.system_program import transfer, TransferParams
            >>> seed = bytes(PublicKey(1))
            >>> sender, receiver = Keypair.from_seed(seed), PublicKey(2)
            >>> transfer_tx = Transaction().add(transfer(TransferParams(from_pubkey=sender.public_key, to_pubkey=receiver, lamports=1000)))
            >>> transfer_tx.recent_blockhash = Blockhash(str(PublicKey(3)))
            >>> transfer_tx.sign(sender)
            >>> transfer_tx.serialize().hex()
            '019d53be8af3a7c30f86c1092d2c3ea61d270c0cfa275a23ba504674c8fbbb724827b23b42dc8e08019e23120f1b6f40f9799355ce54185b4415be37ca2cee6e0e010001034cb5abf6ad79fbf5abbccafcc269d85cd2651ed4b885b5869f241aedf0a5ba2900000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000301020200010c02000000e803000000000000'

        Returns:
            The serialized transaction.
        """  # noqa: E501 pylint: disable=line-too-long
        if self.signatures == [Signature.default() for sig in self.signatures]:
            raise AttributeError("transaction has not been signed")

        if verify_signatures:
            if not self.verify_signatures():
                raise AttributeError("transaction has not been signed correctly")

        return bytes(self._solders)

    @classmethod
    def deserialize(cls, raw_transaction: bytes) -> Transaction:
        """Parse a wire transaction into a Transaction object.

        Example:

            >>> raw_transaction = bytes.fromhex(
            ...     '019d53be8af3a7c30f86c1092d2c3ea61d270c0cfa2'
            ...     '75a23ba504674c8fbbb724827b23b42dc8e08019e23'
            ...     '120f1b6f40f9799355ce54185b4415be37ca2cee6e0'
            ...     'e010001034cb5abf6ad79fbf5abbccafcc269d85cd2'
            ...     '651ed4b885b5869f241aedf0a5ba290000000000000'
            ...     '0000000000000000000000000000000000000000000'
            ...     '0000000200000000000000000000000000000000000'
            ...     '0000000000000000000000000000000000000000000'
            ...     '0000000000000000000000000000000000000000000'
            ...     '000000301020200010c02000000e803000000000000'
            ... )
            >>> type(Transaction.deserialize(raw_transaction))
            <class 'solana.transaction.Transaction'>

        Returns:
            The deserialized transaction.
        """
        return cls.from_solders(SoldersTx.from_bytes(raw_transaction))

    @classmethod
    def populate(cls, message: Message, signatures: List[Signature]) -> Transaction:
        """Populate Transaction object from message and signatures.

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
            >>> from solana.message import Message
            >>> from solders.signature import Signature
            >>> msg = Message.deserialize(raw_message)
            >>> signatures = [Signature(bytes([1] * SIG_LENGTH)), Signature(bytes([2] * SIG_LENGTH))]
            >>> type(Transaction.populate(msg, signatures))
            <class 'solana.transaction.Transaction'>

        Returns:
            The populated transaction.
        """
        message_underlying = message.to_solders()
        return cls.from_solders(SoldersTx.populate(message_underlying, signatures))
