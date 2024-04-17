"""Library to package an atomic sequence of instructions to a transaction."""
from __future__ import annotations

from typing import Any, List, NamedTuple, Optional, Sequence, Tuple, Union

from solders.hash import Hash as Blockhash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.message import Message as SoldersMessage
from solders.presigner import Presigner
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction import Transaction as SoldersTx
from solders.transaction import TransactionError

PACKET_DATA_SIZE = 1280 - 40 - 8
"""Constant for maximum over-the-wire size of a Transaction."""


class NonceInformation(NamedTuple):
    """NonceInformation to be used to build a Transaction."""

    nonce: Blockhash
    """The current Nonce blockhash."""
    nonce_instruction: Instruction
    """AdvanceNonceAccount Instruction."""


def _build_solders_tx(
    recent_blockhash: Optional[Blockhash] = None,
    nonce_info: Optional[NonceInformation] = None,
    fee_payer: Optional[Pubkey] = None,
    instructions: Optional[Sequence[Instruction]] = None,
) -> SoldersTx:
    core_instructions = [] if instructions is None else instructions
    underlying_instructions = (
        core_instructions if nonce_info is None else [nonce_info.nonce_instruction, *core_instructions]
    )
    underlying_blockhash: Optional[Blockhash]
    if nonce_info is not None:
        underlying_blockhash = nonce_info.nonce
    elif recent_blockhash is not None:
        underlying_blockhash = recent_blockhash
    else:
        underlying_blockhash = None
    underlying_fee_payer = None if fee_payer is None else fee_payer
    underlying_blockhash = Blockhash.default() if underlying_blockhash is None else underlying_blockhash
    msg = SoldersMessage.new_with_blockhash(underlying_instructions, underlying_fee_payer, underlying_blockhash)
    return SoldersTx.new_unsigned(msg)


def _decompile_instructions(msg: SoldersMessage) -> List[Instruction]:
    account_keys = msg.account_keys
    decompiled_instructions: List[Instruction] = []
    for compiled_ix in msg.instructions:
        program_id = account_keys[compiled_ix.program_id_index]
        account_metas = [
            AccountMeta(
                account_keys[idx],
                is_signer=msg.is_signer(idx),
                is_writable=msg.is_writable(idx),
            )
            for idx in compiled_ix.accounts
        ]
        decompiled_instructions.append(Instruction(program_id, compiled_ix.data, account_metas))
    return decompiled_instructions


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
        fee_payer: Optional[Pubkey] = None,
        instructions: Optional[Sequence[Instruction]] = None,
    ) -> None:
        """Init transaction object."""
        self._solders = _build_solders_tx(
            recent_blockhash=recent_blockhash,
            nonce_info=nonce_info,
            fee_payer=fee_payer,
            instructions=instructions,
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
        return self._solders.message.recent_blockhash

    @recent_blockhash.setter
    def recent_blockhash(self, blockhash: Optional[Blockhash]) -> None:  # noqa: D102
        self._solders = _build_solders_tx(
            recent_blockhash=blockhash,
            nonce_info=None,
            fee_payer=self.fee_payer,
            instructions=self.instructions,
        )

    @property
    def fee_payer(self) -> Optional[Pubkey]:
        """Optional[Pubkey]: The transaction fee payer."""
        account_keys = self._solders.message.account_keys
        return account_keys[0] if account_keys else None

    @fee_payer.setter
    def fee_payer(self, payer: Optional[Pubkey]) -> None:  # noqa: D102
        self._solders = _build_solders_tx(
            recent_blockhash=self.recent_blockhash,
            nonce_info=None,
            fee_payer=payer,
            instructions=self.instructions,
        )

    @property
    def instructions(self) -> Tuple[Instruction, ...]:
        """Tuple[Instruction]: The instructions contained in this transaction."""
        msg = self._solders.message
        return tuple(_decompile_instructions(msg))

    @instructions.setter
    def instructions(self, ixns: Sequence[Instruction]) -> None:  # noqa: D102
        self._solders = _build_solders_tx(
            recent_blockhash=self.recent_blockhash,
            nonce_info=None,
            fee_payer=self.fee_payer,
            instructions=ixns,
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

    def add(self, *args: Union[Transaction, Instruction]) -> Transaction:
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
            elif isinstance(arg, Instruction):
                self.instructions = (*self.instructions, arg)
            else:
                raise ValueError("invalid instruction:", arg)

        return self

    def compile_message(self) -> Message:  # pylint: disable=too-many-locals
        """Compile transaction data.

        Returns:
            The compiled message.
        """
        return self._solders.message

    def serialize_message(self) -> bytes:
        """Get raw transaction data that need to be covered by signatures.

        Returns:
            The serialized message.
        """
        return bytes(self.compile_message())

    def sign_partial(self, *partial_signers: Keypair) -> None:
        """Partially sign a Transaction with the specified keypairs.

        All the caveats from the `sign` method apply to `sign_partial`
        """
        self._solders.partial_sign(partial_signers, self._solders.message.recent_blockhash)

    def sign(self, *signers: Keypair) -> None:
        """Sign the Transaction with the specified accounts.

        Multiple signatures may be applied to a Transaction. The first signature
        is considered "primary" and is used when testing for Transaction confirmation.

        Transaction fields should not be modified after the first call to `sign`,
        as doing so may invalidate the signature and cause the Transaction to be
        rejected.

        The Transaction must be assigned a valid `recent_blockhash` before invoking this method.
        """
        self._solders.sign(signers, self._solders.message.recent_blockhash)

    def add_signature(self, pubkey: Pubkey, signature: Signature) -> None:
        """Add an externally created signature to a transaction.

        Args:
            pubkey: The public key that created the signature.
            signature: The signature to add.
        """
        presigner = Presigner(pubkey, signature)
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
            >>> from solders.keypair import Keypair
            >>> from solders.pubkey import Pubkey
            >>> from solders.hash import Hash
            >>> from solders.system_program import transfer, TransferParams
            >>> leading_zeros = [0] * 31
            >>> seed = bytes(leading_zeros + [1])
            >>> sender, receiver = Keypair.from_seed(seed), Pubkey(leading_zeros + [2])
            >>> transfer_tx = Transaction().add(transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=receiver, lamports=1000)))
            >>> transfer_tx.recent_blockhash = Hash(leading_zeros + [3])
            >>> transfer_tx.sign(sender)
            >>> transfer_tx.serialize().hex()
            '019d53be8af3a7c30f86c1092d2c3ea61d270c0cfa275a23ba504674c8fbbb724827b23b42dc8e08019e23120f1b6f40f9799355ce54185b4415be37ca2cee6e0e010001034cb5abf6ad79fbf5abbccafcc269d85cd2651ed4b885b5869f241aedf0a5ba2900000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000301020200010c02000000e803000000000000'

        Returns:
            The serialized transaction.
        """  # noqa: E501 pylint: disable=line-too-long
        if self.signatures == [Signature.default() for sig in self.signatures]:
            raise AttributeError("transaction has not been signed")

        if verify_signatures and not self.verify_signatures():
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
            >>> from solders.message import Message
            >>> from solders.signature import Signature
            >>> msg = Message.from_bytes(raw_message)
            >>> signatures = [Signature(bytes([1] * Signature.LENGTH)), Signature(bytes([2] * Signature.LENGTH))]
            >>> type(Transaction.populate(msg, signatures))
            <class 'solana.transaction.Transaction'>

        Returns:
            The populated transaction.
        """
        return cls.from_solders(SoldersTx.populate(message, signatures))
