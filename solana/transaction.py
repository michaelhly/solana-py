"""Library to package an atomic sequence of instructions to a transaction."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, NewType, Optional, Union

from base58 import b58decode, b58encode
from nacl.exceptions import BadSignatureError  # type: ignore
from nacl.signing import VerifyKey  # type: ignore

from solana.account import Account
from solana.blockhash import Blockhash
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
    """Program input."""
    program_id: PublicKey
    """Public keys to include in this transaction Boolean represents whether this
    pubkey needs to sign the transaction.
    """
    data: bytes = bytes(0)
    """Program Id to execute."""


class NonceInformation(NamedTuple):
    """NonceInformation to be used to build a Transaction."""

    nonce: Blockhash
    """The current Nonce blockhash."""
    nonce_instruction: TransactionInstruction
    """AdvanceNonceAccount Instruction."""


@dataclass
class _SigPubkeyPair:
    pubkey: PublicKey
    signature: Optional[bytes] = None


class Transaction:
    """Transaction class to represent an atomic transaction."""

    # Default (empty) signature
    __DEFAULT_SIG = bytes(64)

    def __init__(
        self,
        recent_blockhash: Optional[Blockhash] = None,
        nonce_info: Optional[NonceInformation] = None,
        signatures: Optional[List[_SigPubkeyPair]] = None,
    ) -> None:
        """Init transaction object."""
        self.instructions: List[TransactionInstruction] = []
        self.signatures: List[_SigPubkeyPair] = signatures if signatures else []
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
        """The first (payer) Transaction signature."""
        return None if not self.signatures else self.signatures[0].signature

    def add(self, *args: Union[Transaction, TransactionInstruction]) -> Transaction:
        """Add one or more instructions to this Transaction."""
        for arg in args:
            if isinstance(arg, Transaction):
                self.instructions.extend(arg.instructions)
            elif isinstance(arg, TransactionInstruction):
                self.instructions.append(arg)
            else:
                raise ValueError("invalid instruction:", arg)

        return self

    def compile_message(self) -> Message:
        """Compile transaction data."""
        if self.nonce_info and self.instructions[0] != self.nonce_info.nonce_instruction:
            self.recent_blockhash = self.nonce_info.nonce
            self.instructions = [self.nonce_info.nonce_instruction] + self.instructions

        if not self.recent_blockhash:
            raise AttributeError("transaction recentBlockhash required")
        if len(self.instructions) < 1:
            raise AttributeError("no instructions provided")

        account_metas, program_ids = [], set()
        for instr in self.instructions:
            if not instr.program_id or not instr.keys:
                raise AttributeError("invalid instruction:", instr)
            account_metas.extend(instr.keys)
            program_ids.add(str(instr.program_id))

        # Append programID account metas.
        for pg_id in program_ids:
            account_metas.append(AccountMeta(PublicKey(pg_id), False, False))

        # Prefix accountMetas with feePayer here whenever that gets implemented.

        # Sort. Prioritizing first by signer, then by writable and converting from set to list.
        account_metas.sort(key=lambda account: (not account.is_signer, not account.is_writable))

        # Cull duplicate accounts
        seen: Dict[str, int] = dict()
        uniq_metas: List[AccountMeta] = []
        for sig in self.signatures:
            pubkey = str(sig.pubkey)
            if pubkey in seen:
                uniq_metas[seen[pubkey]].is_signer = True
            else:
                uniq_metas.append(AccountMeta(sig.pubkey, True, True))
                seen[pubkey] = len(uniq_metas) - 1

        for a_m in account_metas:
            pubkey = str(a_m.pubkey)
            if pubkey in seen:
                idx = seen[pubkey]
                uniq_metas[idx].is_writable = uniq_metas[idx].is_writable or a_m.is_writable
            else:
                uniq_metas.append(a_m)
                seen[pubkey] = len(uniq_metas) - 1

        # Split out signing from nonsigning keys and count readonlys
        signed_keys: List[str] = []
        unsigned_keys: List[str] = []
        num_readonly_signed_accounts = num_readonly_unsigned_accounts = 0
        for a_m in uniq_metas:
            if a_m.is_signer:
                # Promote the first signer to writable as it is the fee payer
                if len(signed_keys) != 0 and not a_m.is_writable:
                    num_readonly_signed_accounts += 1
                signed_keys.append(str(a_m.pubkey))
            else:
                num_readonly_unsigned_accounts += int(not a_m.is_writable)
                unsigned_keys.append(str(a_m.pubkey))
        # Initialize signature array, if needed
        if not self.signatures:
            self.signatures = [_SigPubkeyPair(pubkey=PublicKey(key), signature=None) for key in signed_keys]

        account_keys: List[str] = signed_keys + unsigned_keys
        account_indices: Dict[str, int] = {str(key): i for i, key in enumerate(account_keys)}
        compiled_instructions: List[CompiledInstruction] = [
            CompiledInstruction(
                accounts=[account_indices[str(a_m.pubkey)] for a_m in instr.keys],
                program_id_index=account_indices[str(instr.program_id)],
                data=b58encode(instr.data),
            )
            for instr in self.instructions
        ]

        return Message(
            MessageArgs(
                header=MessageHeader(
                    num_required_signatures=len(self.signatures),
                    num_readonly_signed_accounts=num_readonly_signed_accounts,
                    num_readonly_unsigned_accounts=num_readonly_unsigned_accounts,
                ),
                account_keys=account_keys,
                instructions=compiled_instructions,
                recent_blockhash=self.recent_blockhash,
            )
        )

    def serialize_message(self) -> bytes:
        """Get raw transaction data that need to be covered by signatures."""
        return self.compile_message().serialize()

    def sign_partial(self, *partial_signers: Union[PublicKey, Account]) -> None:
        """Partially sign a Transaction with the specified accounts.

        The `Account` inputs will be used to sign the Transaction immediately, while any
        `PublicKey` inputs will be referenced in the signed Transaction but need to
        be filled in later by calling `addSigner()` with the matching `Account`.

        All the caveats from the `sign` method apply to `signPartial`
        """

        def partial_signer_pubkey(account_or_pubkey: Union[PublicKey, Account]):
            return account_or_pubkey.public_key() if isinstance(account_or_pubkey, Account) else account_or_pubkey

        signatures: List[_SigPubkeyPair] = [
            _SigPubkeyPair(pubkey=partial_signer_pubkey(partial_signer)) for partial_signer in partial_signers
        ]
        self.signatures = signatures
        sign_data = self.serialize_message()

        for idx, partial_signer in enumerate(partial_signers):
            if isinstance(partial_signer, Account):
                sig = partial_signer.sign(sign_data).signature
                if len(sig) != SIG_LENGTH:
                    raise RuntimeError("signature has invalid length", sig)
                self.signatures[idx].signature = sig

    def sign(self, *signers: Account) -> None:
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
        if not idx:
            raise ValueError("unknown signer: ", str(pubkey))
        self.signatures[idx].signature = signature

    def add_signer(self, signer: Account) -> None:
        """Fill in a signature for a partially signed Transaction.

        The `signer` must be the corresponding `Account` for a `PublicKey` that was
        previously provided to `signPartial`
        """
        signed_msg = signer.sign(self.serialize_message())
        self.add_signature(signer.public_key(), signed_msg.signature)

    def verify_signatures(self) -> bool:
        """Verify signatures of a complete, signed Transaction."""
        return self.__verify_signatures(self.serialize_message())

    def __verify_signatures(self, signed_data: bytes) -> bool:
        for sig_pair in self.signatures:
            if not sig_pair.signature:
                return False
            try:
                VerifyKey(bytes(sig_pair.pubkey)).verify(signed_data, sig_pair.signature)
            except BadSignatureError:
                return False
        return True

    def serialize(self) -> bytes:
        """Serialize the Transaction in the wire format.

        The Transaction must have a valid `signature` before invoking this method.

        >>> from solana.account import Account
        >>> from solana.blockhash import Blockhash
        >>> from solana.publickey import PublicKey
        >>> from solana.system_program import transfer, TransferParams
        >>> sender, reciever = Account(1), PublicKey(2)
        >>> transfer_tx = Transaction().add(transfer(TransferParams(from_pubkey=sender.public_key(), to_pubkey=reciever, lamports=1000)))
        >>> transfer_tx.recent_blockhash = Blockhash(str(PublicKey(3)))
        >>> transfer_tx.sign(sender)
        >>> transfer_tx.serialize().hex()
        '019d53be8af3a7c30f86c1092d2c3ea61d270c0cfa275a23ba504674c8fbbb724827b23b42dc8e08019e23120f1b6f40f9799355ce54185b4415be37ca2cee6e0e010001034cb5abf6ad79fbf5abbccafcc269d85cd2651ed4b885b5869f241aedf0a5ba2900000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000301020200010c02000000e803000000000000'
        """  # noqa: E501 pylint: disable=line-too-long
        if not self.signatures:
            raise AttributeError("transaction has not been signed")

        sign_data = self.serialize_message()
        if not self.__verify_signatures(sign_data):
            raise AttributeError("transaction has not been signed correctly")

        return self.__serialize(sign_data)

    def __serialize(self, signed_data: bytes) -> bytes:
        if len(self.signatures) >= SIG_LENGTH * 4:
            raise AttributeError("too many singatures to encode")
        wire_transaction = bytearray()
        # Encode signature count
        signature_count = shortvec.encode_length(len(self.signatures))
        wire_transaction.extend(signature_count)
        # Encode signatures
        for sig_pair in self.signatures:
            if not sig_pair.signature:
                continue
            if len(sig_pair.signature) != SIG_LENGTH:
                raise RuntimeError("signature has invalid length", sig_pair.signature)
            wire_transaction.extend(sig_pair.signature)
        # Encode signed data
        wire_transaction.extend(signed_data)

        if len(wire_transaction) > PACKET_DATA_SIZE:
            raise RuntimeError(f"transaction too large: {len(wire_transaction)} > {PACKET_DATA_SIZE}")

        return bytes(wire_transaction)

    @staticmethod
    def deserialize(raw_transaction: bytes) -> Transaction:
        """Parse a wire transaction into a Transaction object.

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
        >>> from base58 import b58encode
        >>> from solana.message import Message
        >>> msg = Message.deserialize(raw_message)
        >>> signatures = [b58encode(bytes([1] * SIG_LENGTH)), b58encode(bytes([2] * SIG_LENGTH))]
        >>> type(Transaction.populate(msg, signatures))
        <class 'solana.transaction.Transaction'>
        """
        transaction = Transaction(recent_blockhash=message.recent_blockhash)

        for idx, sig in enumerate(signatures):
            signature = None if sig == b58encode(Transaction.__DEFAULT_SIG) else b58decode(sig)
            transaction.signatures.append(_SigPubkeyPair(pubkey=message.account_keys[idx], signature=signature))

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
