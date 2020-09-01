"""Library to interface with SPL tokens on Solana."""

from enum import Enum
from typing import List, NamedTuple, Optional

from solana.instruction import InstructionLayout
from solana.publickey import PublicKey

# Instruction Indices
_INITIALIZE_MINT = 0
_INITIALIZE_ACCOUNT = 1
_INITIALIZE_MULTISIG = 2
_TRANSFER = 3
_APPROVE = 4
_REVOKE = 5
_SET_AUTHORITY = 6
_MINT_TO = 7
_BURN = 8
_CLOSE_ACCOUNT = 9
_FREEZE_ACCOUNT = 10
_THAW_ACCOUNT = 11
_TRANSFER2 = 12
_APPROVE2 = 13
_MINT_TO2 = 14
_BURN2 = 15


class AuthorityType(Enum):
    """Specifies the authority type for SetAuthority instructions."""

    MintTokens = 0
    """"Authority to mint new tokens."""
    FreezeAccount = 1
    """Authority to freeze any account associated with the Mint."""
    AccountOwner = 2
    """Owner of a given token account."""
    CloseAccount = 3
    """Authority to close a token account."""


# Instruction Params
class InitializeMintParams(NamedTuple):
    """Initialize token mint transaction params."""

    token_program_id: PublicKey
    """"""
    mint: PublicKey
    """Public key of the minter."""
    mint_authority: PublicKey
    """The authority/multisignature to mint tokens."""
    freeze_authority: Optional[PublicKey]
    """The freeze authority/multisignature of the mint."""
    decimals: int
    """Number of base 10 digits to the right of the decimal place."""


class InitalizeAccountParams(NamedTuple):
    """Initialize token account transaction params."""

    token_program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    mint: PublicKey
    """"""
    owner: PublicKey
    """"""


class InitializeMultisigParams(NamedTuple):
    """Initialize multisig token account transaction params."""

    token_program_id: PublicKey
    """"""
    multisig: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    m: int
    """The number of signers (M) required to validate this multisignature account."""


class TransferParams(NamedTuple):
    """Transfer token transaction params."""

    token_program_id: PublicKey
    """"""
    source: PublicKey
    """"""
    destination: PublicKey
    """"""
    authority: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""


class ApproveParams(NamedTuple):
    """Approve token transaction params."""

    token_program_id: PublicKey
    """"""
    source: PublicKey
    """"""
    delegate: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""


class RevokeParams(NamedTuple):
    """Revoke token transaction params."""

    token_program_id: PublicKey
    """"""
    source: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""


class SetAuthorityParams(NamedTuple):
    """Set token authority transaction params."""

    authority: AuthorityType
    """The type of authority to update."""
    new_authority: Optional[PublicKey] = None
    """The new authority."""


class MintToParams(NamedTuple):
    """Mint token transaction params."""

    token_program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    account: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""


class BurnParams(NamedTuple):
    """Burn token transaction params."""

    token_program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    mint: PublicKey
    """"""
    authority: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""


class CloseAccountParams(NamedTuple):
    """Close token account transaction params."""

    token_program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    destination: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""


class FreezeAccountParams(NamedTuple):
    """Freeze token account transaction params."""

    token_program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    mint: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""


class ThawAccountParams(NamedTuple):
    """Thaw token account transaction params."""

    token_program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    mint: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""


class Transfer2Params(NamedTuple):
    """Transfer2 token transaction params."""

    token_program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    source: PublicKey
    """"""
    destination: PublicKey
    """"""
    authority: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""
    decimal: int
    """"""


class Approve2Params(NamedTuple):
    """Approve2 token transaction params."""

    token_program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    source: PublicKey
    """"""
    delegate: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""
    decimal: int
    """"""


class MintTo2Params(NamedTuple):
    """MintTo2 token transaction params."""

    token_program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    account: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""
    decimal: int
    """"""


class Burn2Params(NamedTuple):
    """Burn2 token transaction params."""

    token_program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    account: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey]
    """"""
    amount: int
    """"""
    decimal: int
    """"""


TOKEN_INSTRUCTION_LAYOUTS: List[InstructionLayout] = [
    InstructionLayout(idx=_INITIALIZE_MINT, fmt="B32s32s"),
    InstructionLayout(idx=_INITIALIZE_ACCOUNT, fmt=""),
    InstructionLayout(idx=_INITIALIZE_MULTISIG, fmt="B"),
    InstructionLayout(idx=_TRANSFER, fmt="Q"),
    InstructionLayout(idx=_APPROVE, fmt="Q"),
    InstructionLayout(idx=_REVOKE, fmt=""),
    InstructionLayout(idx=_SET_AUTHORITY, fmt="I32s"),
    InstructionLayout(idx=_MINT_TO, fmt="Q"),
    InstructionLayout(idx=_BURN, fmt="Q"),
    InstructionLayout(idx=_CLOSE_ACCOUNT, fmt=""),
    InstructionLayout(idx=_FREEZE_ACCOUNT, fmt=""),
    InstructionLayout(idx=_THAW_ACCOUNT, fmt=""),
    InstructionLayout(idx=_TRANSFER2, fmt="QB"),
    InstructionLayout(idx=_APPROVE2, fmt="QB"),
    InstructionLayout(idx=_MINT_TO2, fmt="QB"),
    InstructionLayout(idx=_BURN2, fmt="QB"),
]
