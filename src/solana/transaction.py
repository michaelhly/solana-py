"""Library to package an atomic sequence of instructions to a transaction."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, NewType, Optional, Union

from based58 import b58decode, b58encode
from solders.signature import Signature

from solana.blockhash import Blockhash
from solana.keypair import Keypair
from solana.message import CompiledInstruction, Message, MessageArgs, MessageHeader
from solana.publickey import PublicKey
from solana.utils import shortvec_encoding as shortvec

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


class Transaction:
    """Transaction class to represent an atomic transaction.

    Args:
        recent_blockhash: A recent transaction id.
        nonce_info: Nonce information.
            If populated, transaction will use a durable Nonce hash instead of a `recent_blockhash`.
        signatures: Signatures for the transaction.
            Typically created by invoking the `sign()` method.
        fee_payer: The transaction fee payer.
    """

    # Default (empty) signature
    __DEFAULT_SIG = bytes(64)

    def __init__(
        self,
        recent_blockhash: Optional[Blockhash] = None,
        nonce_info: Optional[NonceInformation] = None,
        signatures: Optional[List[SigPubkeyPair]] = None,
        fee_payer: Optional[PublicKey] = None,
    ) -> None:
        """Init transaction object."""
        self.fee_payer = fee_payer
        self.instructions: List[TransactionInstruction] = []
        self.signatures: List[SigPubkeyPair] = signatures if signatures else []
        self.recent_blockhash, self.nonce_info = recent_blockhash, nonce_info

    def __eq__(self, other: Any) -> bool:
        """Equality defintion for Transactions."""
        if not isinstance(other, Transaction):
            return False
        return (
            self.recent_blockhash == other.recent_blockhash
            and self.nonce_info == other.nonce_info
            and self.signatures == other.signatures
            and self.instructions == other.instructions
        )

    def signature(self) -> Optional[bytes]:
        """The first (payer) Transaction signature.

        Returns:
            The payer signature.
        """
        return None if not self.signatures else self.signatures[0].signature

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
                self.instructions.extend(arg.instructions)
            elif isinstance(arg, TransactionInstruction):
                self.instructions.append(arg)
            else:
                raise ValueError("invalid instruction:", arg)

        return self

    def compile_message(self) -> Message:  # pylint: disable=too-many-locals
        """Compile transaction data.

        Returns:
            The compiled message.
        """
        if self.nonce_info and self.instructions[0] != self.nonce_info.nonce_instruction:
            self.recent_blockhash = self.nonce_info.nonce
            self.instructions = [self.nonce_info.nonce_instruction] + self.instructions

        if not self.recent_blockhash:
            raise AttributeError("transaction recentBlockhash required")
        if len(self.instructions) < 1:
            raise AttributeError("no instructions provided")

        fee_payer = self.fee_payer
        if not fee_payer and len(self.signatures) > 0 and self.signatures[0].pubkey:
            # Use implicit fee payer
            fee_payer = self.signatures[0].pubkey

        if not fee_payer:
            raise AttributeError("transaction feePayer required")

        # Organize account_metas
        account_metas: Dict[str, AccountMeta] = {}

        for instruction in self.instructions:

            if not instruction.program_id:
                raise AttributeError("invalid instruction:", instruction)

            # Update `is_signer` and `is_writable` as iterate through instructions
            for key in instruction.keys:
                pubkey = str(key.pubkey)
                if pubkey not in account_metas:
                    account_metas[pubkey] = key
                else:
                    account_metas[pubkey].is_signer = True if key.is_signer else account_metas[pubkey].is_signer
                    account_metas[pubkey].is_writable = True if key.is_writable else account_metas[pubkey].is_writable

            # Add program_id to account_metas
            instruction_program_id = str(instruction.program_id)
            if instruction_program_id not in account_metas:
                account_metas[instruction_program_id] = AccountMeta(
                    pubkey=instruction.program_id,
                    is_signer=False,
                    is_writable=False,
                )

        # Separate `fee_payer_am` and sort the remaining account_metas
        # Sort keys are:
        # 1. is_signer, with `is_writable`=False ordered last
        # 2. is_writable
        # 3. PublicKey
        fee_payer_am = account_metas.pop(str(fee_payer), None)
        if fee_payer_am:
            fee_payer_am.is_signer = True
            fee_payer_am.is_writable = True
        else:
            fee_payer_am = AccountMeta(fee_payer, True, True)

        sorted_account_metas = sorted(account_metas.values(), key=lambda am: (str(am.pubkey).lower()))
        signer_am = sorted([x for x in sorted_account_metas if x.is_signer], key=lambda am: not am.is_writable)
        writable_am = [x for x in sorted_account_metas if (not x.is_signer and x.is_writable)]
        rest_am = [x for x in sorted_account_metas if (not x.is_signer and not x.is_writable)]

        joined_am = [fee_payer_am] + signer_am + writable_am + rest_am

        # Get signature counts for header

        # The number of signatures required for this message to be considered valid. The
        # signatures must match the first `num_required_signatures` of `account_keys`.
        # NOTE: Serialization-related changes must be paired with the direct read at sigverify.
        num_required_signatures: int = len([x for x in joined_am if x.is_signer])
        # The last num_readonly_signed_accounts of the signed keys are read-only accounts. Programs
        # may process multiple transactions that load read-only accounts within a single PoH entry,
        # but are not permitted to credit or debit lamports or modify account data. Transactions
        # targeting the same read-write account are evaluated sequentially.
        num_readonly_signed_accounts: int = len([x for x in joined_am if (not x.is_writable and x.is_signer)])
        # The last num_readonly_unsigned_accounts of the unsigned keys are read-only accounts.
        num_readonly_unsigned_accounts: int = len([x for x in joined_am if (not x.is_writable and not x.is_signer)])

        # Initialize signature array, if needed
        account_keys = [(str(x.pubkey), x.is_signer) for x in joined_am]

        self.signatures = [] if not self.signatures else self.signatures
        existing_signature_pubkeys: List[str] = [str(x.pubkey) for x in self.signatures]

        # Append missing signatures
        signer_pubkeys = [k for (k, is_signer) in account_keys if is_signer]
        for signer_pubkey in signer_pubkeys:
            if signer_pubkey not in existing_signature_pubkeys:
                self.signatures.append(SigPubkeyPair(pubkey=PublicKey(signer_pubkey), signature=None))

        # Ensure fee_payer signature is first
        fee_payer_signature = [x for x in self.signatures if x.pubkey == fee_payer]
        other_signatures = [x for x in self.signatures if x.pubkey != fee_payer]
        self.signatures = fee_payer_signature + other_signatures

        account_indices: Dict[str, int] = {k: idx for idx, (k, _) in enumerate(account_keys)}

        compiled_instructions: List[CompiledInstruction] = [
            CompiledInstruction(
                accounts=[account_indices[str(am.pubkey)] for am in instruction.keys],
                program_id_index=account_indices[str(instruction.program_id)],
                data=b58encode(instruction.data),
            )
            for instruction in self.instructions
        ]

        return Message(
            MessageArgs(
                header=MessageHeader(
                    num_required_signatures=num_required_signatures,
                    num_readonly_signed_accounts=num_readonly_signed_accounts,
                    num_readonly_unsigned_accounts=num_readonly_unsigned_accounts,
                ),
                account_keys=[k for (k, _) in account_keys],
                instructions=compiled_instructions,
                recent_blockhash=self.recent_blockhash,
            )
        )

    def serialize_message(self) -> bytes:
        """Get raw transaction data that need to be covered by signatures.

        Returns:
            The serialized message.
        """
        return self.compile_message().serialize()

    def sign_partial(self, *partial_signers: Union[PublicKey, Keypair]) -> None:
        """Partially sign a Transaction with the specified accounts.

        The `Keypair` inputs will be used to sign the Transaction immediately, while any
        `PublicKey` inputs will be referenced in the signed Transaction but need to
        be filled in later by calling `addSigner()` with the matching `Keypair`.

        All the caveats from the `sign` method apply to `signPartial`
        """

        def partial_signer_pubkey(account_or_pubkey: Union[PublicKey, Keypair]):
            return account_or_pubkey.public_key if isinstance(account_or_pubkey, Keypair) else account_or_pubkey

        signatures: List[SigPubkeyPair] = [
            SigPubkeyPair(pubkey=partial_signer_pubkey(partial_signer)) for partial_signer in partial_signers
        ]
        self.signatures = signatures
        sign_data = self.serialize_message()

        for idx, partial_signer in enumerate(partial_signers):
            if isinstance(partial_signer, Keypair):
                sig = bytes(partial_signer.sign(sign_data))
                if len(sig) != SIG_LENGTH:
                    raise RuntimeError("signature has invalid length", sig)
                self.signatures[idx].signature = sig

    def sign(self, *signers: Keypair) -> None:
        """Sign the Transaction with the specified accounts.

        Multiple signatures may be applied to a Transaction. The first signature
        is considered "primary" and is used when testing for Transaction confirmation.

        Transaction fields should not be modified after the first call to `sign`,
        as doing so may invalidate the signature and cause the Transaction to be
        rejected.

        The Transaction must be assigned a valid `recentBlockhash` before invoking this method.
        """
        self.sign_partial(*signers)

    def add_signature(self, pubkey: PublicKey, signature: bytes) -> None:
        """Add an externally created signature to a transaction."""
        if len(signature) != SIG_LENGTH:
            raise ValueError("signature has invalid length", signature)
        idx = next((i for i, sig_pair in enumerate(self.signatures) if sig_pair.pubkey == pubkey), None)
        if idx is None:
            raise ValueError("unknown signer: ", str(pubkey))
        self.signatures[idx].signature = signature

    def add_signer(self, signer: Keypair) -> None:
        """Fill in a signature for a partially signed Transaction.

        The `signer` must be the corresponding `Keypair` for a `PublicKey` that was
        previously provided to `signPartial`
        """
        signature = bytes(signer.sign(self.serialize_message()))
        self.add_signature(signer.public_key, signature)

    def verify_signatures(self) -> bool:
        """Verify signatures of a complete, signed Transaction.

        Returns:
            a bool indicating if the signatures are correct or not.
        """
        return self.__verify_signatures(self.serialize_message())

    def __verify_signatures(self, signed_data: bytes) -> bool:
        for sig_pair in self.signatures:
            if not sig_pair.signature:
                return False
            sig = Signature(sig_pair.signature)
            if not sig.verify(sig_pair.pubkey.to_solders(), signed_data):
                return False
        return True

    def serialize(self) -> bytes:
        """Serialize the Transaction in the wire format.

        The Transaction must have a valid `signature` before invoking this method.

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
        if not self.signatures:
            raise AttributeError("transaction has not been signed")

        sign_data = self.serialize_message()
        if not self.__verify_signatures(sign_data):
            raise AttributeError("transaction has not been signed correctly")

        return self.__serialize(sign_data)

    def __serialize(self, signed_data: bytes) -> bytes:
        if len(self.signatures) >= SIG_LENGTH * 4:
            raise AttributeError("too many signatures to encode")
        wire_transaction = bytearray()
        # Encode signature count
        signature_count = shortvec.encode_length(len(self.signatures))
        wire_transaction.extend(signature_count)
        # Encode signatures
        for sig_pair in self.signatures:
            if sig_pair.signature and len(sig_pair.signature) != SIG_LENGTH:
                raise RuntimeError("signature has invalid length", sig_pair.signature)

            if not sig_pair.signature:
                wire_transaction.extend(bytearray(SIG_LENGTH))
            else:
                wire_transaction.extend(sig_pair.signature)
        # Encode signed data
        wire_transaction.extend(signed_data)

        if len(wire_transaction) > PACKET_DATA_SIZE:
            raise RuntimeError(f"transaction too large: {len(wire_transaction)} > {PACKET_DATA_SIZE}")

        return bytes(wire_transaction)

    @staticmethod
    def deserialize(raw_transaction: bytes) -> Transaction:
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
        signatures = []
        signature_count, offset = shortvec.decode_length(raw_transaction)
        for _ in range(signature_count):
            signatures.append(b58encode(raw_transaction[offset : offset + SIG_LENGTH]))  # noqa: E203
            offset += SIG_LENGTH
        return Transaction.populate(Message.deserialize(raw_transaction[offset:]), signatures)

    @staticmethod
    def populate(message: Message, signatures: List[bytes]) -> Transaction:
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
            >>> from based58 import b58encode
            >>> from solana.message import Message
            >>> msg = Message.deserialize(raw_message)
            >>> signatures = [b58encode(bytes([1] * SIG_LENGTH)), b58encode(bytes([2] * SIG_LENGTH))]
            >>> type(Transaction.populate(msg, signatures))
            <class 'solana.transaction.Transaction'>

        Returns:
            The populated transaction.
        """
        transaction = Transaction(recent_blockhash=message.recent_blockhash)

        for idx, sig in enumerate(signatures):
            signature = None if sig == b58encode(Transaction.__DEFAULT_SIG) else b58decode(sig)
            transaction.signatures.append(SigPubkeyPair(pubkey=message.account_keys[idx], signature=signature))

        for instr in message.instructions:
            account_metas: List[AccountMeta] = []
            for acc_idx in instr.accounts:
                pubkey = message.account_keys[acc_idx]
                is_signer = any((pubkey == sigkeypair.pubkey for sigkeypair in transaction.signatures))
                account_metas.append(
                    AccountMeta(pubkey=pubkey, is_signer=is_signer, is_writable=message.is_account_writable(acc_idx))
                )
            program_id = message.account_keys[instr.program_id_index]
            transaction.instructions.append(
                TransactionInstruction(keys=account_metas, program_id=program_id, data=b58decode(instr.data))
            )

        return transaction
