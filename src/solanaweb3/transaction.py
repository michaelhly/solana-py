"""Library to package an atomic sequence of instructions to a transaction."""
from typing import List, NamedTuple, NewType, Union

from solanaweb3.blockhash import Blockhash

TransactionSignatureType = NewType("TransactionSignature", str)

# Maximum over-the-wire size of a Transaction
PACKET_DATA_SIZE = 1280 - 40 - 8


class AccountMeta(NamedTuple):
    """Account metadata used to define instructions."""

    pubkey: "PublicKey"
    is_signer: bool
    is_writable: bool


class TransactionInstructionCtorFields(NamedTuple):
    """List of TransactionInstruction object fields that may be initialized at construction.

    `keys` -  Public keys to include in this transaction. Boolean represents whether this
    pubkey needs to sign the transaction.\n
    `program_id` - The program id to execute.\n
    `data` - The program input.\n
    """

    keys: List["AccountMeta"] = []
    program_id: "PublicKey" = None
    data: bytes = bytes(0)


class TransactionIntruction: # pylint: disable=too-few-public-methods
    """Transaction Instruction containing all metadata of a transaction."""

    def __init__(
        self,
        keys: List["AccountMeta"],
        program_id: Union["PublicKey", None],
        data: bytes,
    ) -> None:
        self.keys, self.program_id, self.data = keys, program_id, data


class NonceInformation(NamedTuple):
    """NonceInformation to be used to build a Transaction."""

    nonce: Blockhash
    nonce_instruction: "TransactionIntruction"


class SignaturePubkeyPair(NamedTuple):
    """Mapping of signature to public key"""

    pubkey: "PublicKey"
    signature: bytes = None


class TransactionCtorFields(NamedTuple):
    """List of Transaction object fields that may be initialized at construction."""

    recent_blockhash: Blockhash = None
    nonce_info: "NonceInformation" = None
    signatures: List["SignaturePubkeyPair"] = []


class Transaction:
    """Transaction class to represent an atomic transaction."""

    # Signatures are 64 bytes in length
    SIG_LENGTH = 64
    # Default (empty) signature
    DEFAULT_SIG = bytes(64)

    def __init__(
        self,
        recent_blockhash: Union[Blockhash, None],
        nonce_info: Union["NonceInformation", None],
        signatures: List["SignaturePubkeyPair"],
    ) -> None:
        self.instructions = []
        self.recent_blockhash, self.nonce_info, self.sigantures = (
            recent_blockhash,
            nonce_info,
            signatures,
        )

    def signature(self) -> Union[bytes, None]:
        """The first (payer) Transaction signature"""
        return None if not self.sigantures else self.sigantures[0].signature

    def add(
        self,
        *args: Union[
            "Transaction", "TransactionIntruction", "TransactionInstructionCtorFields"
        ]
    ) -> None:
        """Add one or more instructions to this Transaction."""
        for arg in args:
            if hasattr(arg, "instructions"):
                self.instructions.extend(arg.instructions)
            if isinstance(arg, TransactionIntruction):
                self.instructions.append(arg)
            else:
                self.instructions.append(TransactionIntruction(*arg))

    def compile_message(self) -> "Message":
        """Compile transaction data."""
        raise NotImplementedError("compile_message not implemented")

    def serialize_message(self) -> bytes:
        """Get raw transaction data that need to be covered by signatures"""
        return self.compile_message().serialize()

    def sign_partial(
        self, *partial_signers: List[Union["PublicKey", "Account"]]
    ) -> None:
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
        if len(signature) != self.SIG_LENGTH:
            raise ValueError(
                "Signature `{}` does not have the correct format".format(signature)
            )
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
    def populate(
        message: "Message", signatures: List[Union[str, bytes]]
    ) -> "Transaction":
        """Populate Transaction object from message and signatures"""
        raise NotImplementedError("populate not implemented")
