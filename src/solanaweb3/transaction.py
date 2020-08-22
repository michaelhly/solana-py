"""Library to package an atomic sequence of instructions to a transaction."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, NamedTuple, NewType, Optional, Union

from base58 import b58decode, b58encode

from solanaweb3.account import Account
from solanaweb3.blockhash import Blockhash
from solanaweb3.message import CompiledInstruction, Message, MessageArgs, MessageHeader
from solanaweb3.publickey import PublicKey

TransactionSignature = NewType("TransactionSignature", str)

# Maximum over-the-wire size of a Transaction
PACKET_DATA_SIZE = 1280 - 40 - 8
# Signatures are 64 bytes in length
SIG_LENGTH = 64


@dataclass
class AccountMeta:
    """Account metadata dataclass.

    :param pubkey: PublicKey

    :param is_signer: bool

    :param is_writable: bool
    """

    pubkey: PublicKey
    is_signer: bool
    is_writable: bool


class TransactionInstruction(NamedTuple):
    """List of TransactionInstruction object fields that may be initialized at construction.

    :param keys: List[AccountMeta]

    :param program_id: PublicKey

    :param data: bytes = bytes(0)
    """

    keys: List[AccountMeta]
    program_id: PublicKey
    data: bytes = bytes(0)


class NonceInformation(NamedTuple):
    """NonceInformation to be used to build a Transaction.

    :param nonce: Blockhash

    :param nonce_instruction: "TransactionIntruction"
    """

    nonce: Blockhash
    nonce_instruction: TransactionInstruction


class _SigPubkeyPair(NamedTuple):
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

    def signature(self) -> Optional[bytes]:
        """First (payer) Transaction signature."""
        return None if not self.signatures else self.signatures[0].signature

    def add(self, *args: Union[Transaction, TransactionInstruction]) -> None:
        """Add one or more instructions to this Transaction."""
        for arg in args:
            if hasattr(arg, "instructions"):
                self.instructions.extend(arg.instructions)  # type: ignore
            elif isinstance(arg, TransactionInstruction):
                self.instructions.append(arg)
            else:
                raise ValueError("invalid instruction:", arg)

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
        raise NotImplementedError("sign_partial not implemented")

    def sign(self, *signers: Account) -> None:
        """Sign the Transaction with the specified accounts.

        Multiple signatures may be applied to a Transaction. The first signature
        is considered "primary" and is used when testing for Transaction confirmation.

        Transaction fields should not be modified after the first call to `sign`,
        as doing so may invalidate the signature and cause the Transaction to be
        rejected.

        The Transaction must be assigned a valid `recentBlockhash` before invoking this method
        """
        self.sign_partial(*signers)

    def add_signature(self, pubkey: PublicKey, signature: bytes) -> None:
        """Add an externally created signature to a transaction."""
        raise NotImplementedError("add_signature not implemented")

    def add_signer(self, signer: Account) -> None:
        """Fill in a signature for a partially signed Transaction.

        The `signer` must be the corresponding `Account` for a `PublicKey` that was
        previously provided to `signPartial`
        """
        msg = self.serialize_message()
        signed_msg = signer.sign(msg)
        self.add_signature(signer.public_key(), signed_msg)

    def __verify_signatures(self, signed_data: bytes) -> bool:
        raise NotImplementedError("__verify_signatures not implemented")

    def serialize(self) -> bytes:
        """Serialize the Transaction in the wire format.

        The Transaction must have a valid `signature` before invoking this method.
        """
        raise NotImplementedError("serialize not implemented")

    def __serialize(self, signed_data: bytes) -> bytes:
        raise NotImplementedError("__serialize not implemented")

    @staticmethod
    def deserialize(raw_transaction: bytes) -> Transaction:
        """Parse a wire transaction into a Transaction object."""
        raise NotImplementedError("deserialize not implemented")

    @staticmethod
    def populate(message: Message, signatures: List[Union[str, bytes]]) -> Transaction:
        """Populate Transaction object from message and signatures."""
        transaction = Transaction()
        transaction.recent_blockhash = message.recent_blockhash

        for idx, sig in enumerate(signatures):
            signature = b58encode(Transaction.__DEFAULT_SIG)
            if sig:
                signature = b58decode(sig) if isinstance(sig, str) else b58encode(sig)
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
