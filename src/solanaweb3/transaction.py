"""Library to package an atomic sequence of instructions to a transaction."""
from typing import List, NamedTuple, NewType, Union

from base58 import b58encode

from solanaweb3.blockhash import Blockhash
from solanaweb3.message import Message, MessageArgs, MessageHeader, CompiledInstruction
from solanaweb3.publickey import PublicKey

TransactionSignatureType = NewType("TransactionSignature", str)

# Maximum over-the-wire size of a Transaction
PACKET_DATA_SIZE = 1280 - 40 - 8


class AccountMeta(NamedTuple):
    """Account metadata used to define instructions.

    pubkey: "PublicKey"\n
    is_signer: bool\n
    is_writable: bool\n
    """

    pubkey: "PublicKey"
    is_signer: bool
    is_writable: bool


class TransactionInstruction(NamedTuple):
    """List of TransactionInstruction object fields that may be initialized at construction.

    keys: List["AccountMeta"] = []\n
    program_id: "PublicKey" = None\n
    data: bytes = bytes(0)\n
    """

    keys: List["AccountMeta"] = []
    program_id: "PublicKey" = None
    data: bytes = bytes(0)


class NonceInformation(NamedTuple):
    """NonceInformation to be used to build a Transaction.

    nonce: Blockhash\n
    nonce_instruction: "TransactionIntruction"\n
    """

    nonce: Blockhash
    nonce_instruction: "TransactionIntruction"


class SignaturePubkeyPair(NamedTuple):
    """Mapping of signature to public key

    pubkey: "PublicKey"\n
    signature: bytes = None\n
    """

    pubkey: "PublicKey"
    signature: bytes = None


class TransactionCtorFields(NamedTuple):
    """List of Transaction object fields that may be initialized at construction.

    recent_blockhash: Blockhash = None\n
    nonce_info: "NonceInformation" = None\n
    signatures: List["SignaturePubkeyPair"] = []\n
    """

    recent_blockhash: Blockhash = None
    nonce_info: "NonceInformation" = None
    signatures: List["SignaturePubkeyPair"] = []


class Transaction:
    """Transaction class to represent an atomic transaction."""

    # Signatures are 64 bytes in length
    __SIG_LENGTH = 64
    # Default (empty) signature
    __DEFAULT_SIG = bytes(64)

    def __init__(
        self,
        recent_blockhash: Union[Blockhash, None],
        nonce_info: Union["NonceInformation", None],
        signatures: List["SignaturePubkeyPair"],
    ) -> None:
        self.instructions: List["TransactionInstruction"] = []
        self.recent_blockhash, self.nonce_info, self.signatures = (
            recent_blockhash,
            nonce_info,
            signatures,
        )

    def signature(self) -> Union[bytes, None]:
        """The first (payer) Transaction signature"""
        return None if not self.signatures else self.signatures[0].signature

    def add(self, *args: Union["Transaction", "TransactionIntruction"]) -> None:
        """Add one or more instructions to this Transaction."""
        for arg in args:
            if hasattr(arg, "instructions"):
                self.instructions.extend(arg.instructions)
            elif isinstance(arg, TransactionInstruction):
                self.instructions.append(arg)
            else:
                raise ValueError("invalid instruction {}".format(arg))

    def compile_message(self) -> "Message":
        """Compile transaction data."""
        if self.nonce_info and self.instructions[0] != self.nonce_info.nonce_instruction:
            self.recent_blockhash = self.nonce_info.nonce
            self.instructions = [self.nonce_info.nonce_instruction] + self.instructions

        if not self.recent_blockhash:
            raise AttributeError("Transaction recentBlockhash required")
        if len(self.instructions) < 1:
            raise AttributeError("No instructions provided")

        account_metas, program_ids = [], set()
        for instr in self.instructions:
            if not instr.program_id or not instr.keys:
                raise AttributeError("Invalid instruction {}".format(instr))
            account_metas = account_metas.extend(instr.keys)
            program_ids.add(str(instr.program_id))

        # Append programID account metas.
        for pg_id in program_ids:
            account_metas.add(AccountMeta(pubkey=PublicKey(pg_id), is_signer=False, is_writable=False))

        # Prefix accountMetas with feePayer here whenever that gets implemented.

        # Sort. Prioritizing first by signer, then by writable and converting from set to list.
        account_metas.sort(key=lambda account: (account.is_signer, account.is_writable))

        # Cull duplicate accounts
        seen, uniq_metas = dict(), []
        for sig in self.signatures:
            pubkey = str(sig.pubkey)
            if pubkey in seen:
                uniq_metas[seen[pubkey]].is_signer = True
            else:
                uniq_metas.append(AccountMeta(pubkey=sig.pubkey, is_signer=True, is_writable=True))
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
        signed_keys, unsigned_keys = [], []
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
            self.signatures = [SignaturePubkeyPair(pubkey=PublicKey(key), signature=None) for key in signed_keys]

        account_keys = signed_keys.extend(unsigned_keys)
        account_indices = {str(key): i for key, i in enumerate(account_keys)}
        compiled_instructions = [
            CompiledInstruction(
                accounts=[account_indices[str(key)] for key in instr.keys],
                program_id_idx=account_indices[str(instr.program_id)],
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
        """Get raw transaction data that need to be covered by signatures"""
        return self.compile_message().serialize()

    def sign_partial(self, *partial_signers: List[Union["PublicKey", "Account"]]) -> None:
        """Partially sign a Transaction with the specified accounts.  The `Account`
        inputs will be used to sign the Transaction immediately, while any
        `PublicKey` inputs will be referenced in the signed Transaction but need to
        be filled in later by calling `addSigner()` with the matching `Account`.

        All the caveats from the `sign` method apply to `signPartial`
        """
        raise NotImplementedError("sign_partial not implemented")

    def sign(self, *signers: List["Account"]) -> None:
        """Sign the Transaction with the specified accounts.  Multiple signatures may
        be applied to a Transaction. The first signature is considered "primary"
        and is used when testing for Transaction confirmation.

        Transaction fields should not be modified after the first call to `sign`,
        as doing so may invalidate the signature and cause the Transaction to be
        rejected.

        The Transaction must be assigned a valid `recentBlockhash` before invoking this method
        """
        self.sign_partial(*signers)

    def add_signature(self, pubkey: "PublicKey", signature: bytes) -> None:
        """Add an externally created signature to a transaction"""
        if len(signature) != self.__SIG_LENGTH:
            raise ValueError("Signature `{}` does not have the correct format".format(signature))
        raise NotImplementedError("add_signature not implemented")

    def add_signer(self, signer: "Account") -> None:
        """Fill in a signature for a partially signed Transaction.  The `signer` must
        be the corresponding `Account` for a `PublicKey` that was previously provided to
        `signPartial`
        """
        msg = self.serialize_message()
        signed_msg = signer.sign(msg)
        self.add_signature(signer.public_key, signed_msg)

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
    def deserialize(raw_transaction: bytes) -> "Transaction":
        """Parse a wire transaction into a Transaction object."""
        raise NotImplementedError("deserialize not implemented")

    @staticmethod
    def populate(message: "Message", signatures: List[Union[str, bytes]]) -> "Transaction":
        """Populate Transaction object from message and signatures"""
        raise NotImplementedError("populate not implemented")
