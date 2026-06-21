"""Pydantic models for SPL token types.

These are the Pydantic successors to the deprecated ``NamedTuple`` types in
:mod:`spl.token.core` (account/mint info) and :mod:`spl.token.instructions` (instruction
params). They carry the same field names and defaults, so migrating is a matter of
changing the import path.
"""

from __future__ import annotations

from enum import IntEnum
from typing import List, Optional

from solders.pubkey import Pubkey

from solana._pydantic import PydanticModel


class AuthorityType(IntEnum):
    """Specifies the authority type for SetAuthority instructions."""

    MINT_TOKENS = 0
    """"Authority to mint new tokens."""
    FREEZE_ACCOUNT = 1
    """Authority to freeze any account associated with the Mint."""
    ACCOUNT_OWNER = 2
    """Owner of a given token account."""
    CLOSE_ACCOUNT = 3
    """Authority to close a token account."""


class AccountInfo(PydanticModel):
    """Information about an account."""

    mint: Pubkey
    """The mint associated with this account."""
    owner: Pubkey
    """Owner of this account."""
    amount: int
    """Amount of tokens this account holds."""
    delegate: Optional[Pubkey]
    """The delegate for this account."""
    delegated_amount: int
    """The amount of tokens the delegate authorized to the delegate."""
    is_initialized: bool
    """ Is this account initialized."""
    is_frozen: bool
    """Is this account frozen."""
    is_native: bool
    """Is this a native token account."""
    rent_exempt_reserve: Optional[int]
    """If this account is a native token, it must be rent-exempt.

    This value logs the rent-exempt reserve which must remain in the balance
    until the account is closed.
    """
    close_authority: Optional[Pubkey]
    """Optional authority to close the account."""


class MintInfo(PydanticModel):
    """Information about the mint."""

    mint_authority: Optional[Pubkey]
    """"Optional authority used to mint new tokens.

    The mint authority may only be provided during mint creation. If no mint
    authority is present then the mint has a fixed supply and no further tokens
    may be minted.
    """
    supply: int
    """Total supply of tokens."""
    decimals: int
    """Number of base 10 digits to the right of the decimal place."""
    is_initialized: bool
    """Is this mint initialized."""
    freeze_authority: Optional[Pubkey]
    """ Optional authority to freeze token accounts."""


class InitializeMintParams(PydanticModel):
    """Initialize token mint transaction params."""

    decimals: int
    """Number of base 10 digits to the right of the decimal place."""
    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Public key of the minter account."""
    mint_authority: Pubkey
    """The authority/multisignature to mint tokens."""
    freeze_authority: Optional[Pubkey] = None
    """The freeze authority/multisignature of the mint."""


class InitializeMint2Params(PydanticModel):
    """Initialize token mint transaction params without Rent sysvar."""

    decimals: int
    """Number of base 10 digits to the right of the decimal place."""
    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Public key of the minter account."""
    mint_authority: Pubkey
    """The authority/multisignature to mint tokens."""
    freeze_authority: Optional[Pubkey] = None
    """The freeze authority/multisignature of the mint."""


class InitializeAccountParams(PydanticModel):
    """Initialize token account transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Public key of the new account."""
    mint: Pubkey
    """Public key of the minter account."""
    owner: Pubkey
    """Owner of the new account."""


class InitializeAccount2Params(PydanticModel):
    """Initialize token account transaction params with owner in instruction data."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Public key of the new account."""
    mint: Pubkey
    """Public key of the minter account."""
    owner: Pubkey
    """Owner of the new account."""


class InitializeAccount3Params(PydanticModel):
    """Initialize token account transaction params with owner in instruction data and no Rent sysvar."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Public key of the new account."""
    mint: Pubkey
    """Public key of the minter account."""
    owner: Pubkey
    """Owner of the new account."""


class InitializeMultisigParams(PydanticModel):
    """Initialize multisig token account transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    multisig: Pubkey
    """New multisig account address."""
    m: int
    """The number of signers (M) required to validate this multisignature account."""
    signers: List[Pubkey] = []
    """Addresses of multisig signers."""


class InitializeMultisig2Params(PydanticModel):
    """Initialize multisig token account transaction params without Rent sysvar."""

    program_id: Pubkey
    """SPL Token program account."""
    multisig: Pubkey
    """New multisig account address."""
    m: int
    """The number of signers (M) required to validate this multisignature account."""
    signers: List[Pubkey] = []
    """Addresses of multisig signers."""


class TransferParams(PydanticModel):
    """Transfer token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    source: Pubkey
    """Source account."""
    dest: Pubkey
    """Destination account."""
    owner: Pubkey
    """Owner of the source account."""
    amount: int
    """Number of tokens to transfer."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig."""


class ApproveParams(PydanticModel):
    """Approve token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    source: Pubkey
    """Source account."""
    delegate: Pubkey
    """Delegate account authorized to perform a transfer of tokens from the source account."""
    owner: Pubkey
    """Owner of the source account."""
    amount: int
    """Maximum number of tokens the delegate may transfer."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig."""


class RevokeParams(PydanticModel):
    """Revoke token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Source account for which transfer authority is being revoked."""
    owner: Pubkey
    """Owner of the source account."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig."""


class SetAuthorityParams(PydanticModel):
    """Set token authority transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Public key of the token account."""
    authority: AuthorityType
    """The type of authority to update."""
    current_authority: Pubkey
    """Current authority of the specified type."""
    signers: List[Pubkey] = []
    """Signing accounts if `current_authority` is a multiSig."""
    new_authority: Optional[Pubkey] = None
    """New authority of the account."""


class MintToParams(PydanticModel):
    """Mint token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Public key of the minter account."""
    dest: Pubkey
    """Public key of the account to mint to."""
    mint_authority: Pubkey
    """The mint authority."""
    amount: int
    """Amount to mint."""
    signers: List[Pubkey] = []
    """Signing accounts if `mint_authority` is a multiSig."""


class BurnParams(PydanticModel):
    """Burn token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Account to burn tokens from."""
    mint: Pubkey
    """Public key of the minter account."""
    owner: Pubkey
    """Owner of the account."""
    amount: int
    """Amount to burn."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig"""


class CloseAccountParams(PydanticModel):
    """Close token account transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Address of account to close."""
    dest: Pubkey
    """Address of account to receive the remaining balance of the closed account."""
    owner: Pubkey
    """Owner of the account."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig"""


class FreezeAccountParams(PydanticModel):
    """Freeze token account transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Account to freeze."""
    mint: Pubkey
    """Public key of the minter account."""
    authority: Pubkey
    """Mint freeze authority"""
    multi_signers: List[Pubkey] = []
    """Signing accounts if `authority` is a multiSig"""


class ThawAccountParams(PydanticModel):
    """Thaw token account transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Account to thaw."""
    mint: Pubkey
    """Public key of the minter account."""
    authority: Pubkey
    """Mint freeze authority"""
    multi_signers: List[Pubkey] = []
    """Signing accounts if `authority` is a multiSig"""


class TransferCheckedParams(PydanticModel):
    """TransferChecked token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    source: Pubkey
    """Source account."""
    mint: Pubkey
    """Public key of the minter account."""
    dest: Pubkey
    """Destination account."""
    owner: Pubkey
    """Owner of the source account."""
    amount: int
    """Number of tokens to transfer."""
    decimals: int
    """Amount decimals."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig."""


class ApproveCheckedParams(PydanticModel):
    """ApproveChecked token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    source: Pubkey
    """Source account."""
    mint: Pubkey
    """Public key of the minter account."""
    delegate: Pubkey
    """Delegate account authorized to perform a transfer of tokens from the source account."""
    owner: Pubkey
    """Owner of the source account."""
    amount: int
    """Maximum number of tokens the delegate may transfer."""
    decimals: int
    """Amount decimals."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig."""


class MintToCheckedParams(PydanticModel):
    """MintToChecked token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Public key of the minter account."""
    dest: Pubkey
    """Public key of the account to mint to."""
    mint_authority: Pubkey
    """The mint authority."""
    amount: int
    """Amount to mint."""
    decimals: int
    """Amount decimals."""
    signers: List[Pubkey] = []
    """Signing accounts if `mint_authority` is a multiSig."""


class BurnCheckedParams(PydanticModel):
    """BurnChecked token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Public key of the minter account."""
    account: Pubkey
    """Account to burn tokens from."""
    owner: Pubkey
    """Owner of the account."""
    amount: int
    """Amount to burn."""
    decimals: int
    """Amount decimals."""
    signers: List[Pubkey] = []
    """Signing accounts if `owner` is a multiSig"""


class SyncNativeParams(PydanticModel):
    """BurnChecked token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Account to sync."""


class GetAccountDataSizeParams(PydanticModel):
    """GetAccountDataSize token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Mint to calculate account size for."""


class InitializeImmutableOwnerParams(PydanticModel):
    """InitializeImmutableOwner token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    account: Pubkey
    """Token account to initialize immutable owner for."""


class InitializeTransferFeeConfigParams(PydanticModel):
    """InitializeTransferFeeConfig token transaction params."""

    program_id: Pubkey
    """SPL Token 2022 program account."""
    mint: Pubkey
    """Mint to initialize transfer fee config for."""
    transfer_fee_config_authority: Optional[Pubkey]
    """Authority that may update the transfer fee config."""
    withdraw_withheld_authority: Optional[Pubkey]
    """Authority that may withdraw withheld tokens."""
    transfer_fee_basis_points: int
    """Amount of transfer collected as fees, expressed in basis points."""
    maximum_fee: int
    """Maximum fee assessed on transfers."""


class WithdrawWithheldTokensFromAccountsParams(PydanticModel):
    """WithdrawWithheldTokensFromAccounts token transaction params."""

    program_id: Pubkey
    """SPL Token 2022 program account."""
    mint: Pubkey
    """Mint that includes the TransferFeeConfig extension."""
    dest: Pubkey
    """Fee receiver token account."""
    authority: Pubkey
    """Withdraw withheld authority."""
    signers: List[Pubkey] = []
    """Signing accounts if `authority` is a multiSig."""
    sources: List[Pubkey] = []
    """Token accounts to withdraw withheld tokens from."""


class WithdrawWithheldTokensFromMintParams(PydanticModel):
    """WithdrawWithheldTokensFromMint token transaction params."""

    program_id: Pubkey
    """SPL Token 2022 program account."""
    mint: Pubkey
    """Mint that includes the TransferFeeConfig extension."""
    dest: Pubkey
    """Fee receiver token account."""
    authority: Pubkey
    """Withdraw withheld authority."""
    signers: List[Pubkey] = []
    """Signing accounts if `authority` is a multiSig."""


class HarvestWithheldTokensToMintParams(PydanticModel):
    """HarvestWithheldTokensToMint token transaction params."""

    program_id: Pubkey
    """SPL Token 2022 program account."""
    mint: Pubkey
    """Mint to harvest withheld tokens to."""
    sources: List[Pubkey] = []
    """Token accounts to harvest withheld tokens from."""


class AmountToUiAmountParams(PydanticModel):
    """AmountToUiAmount token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Mint to use for conversion."""
    amount: int
    """Amount of tokens to reformat."""


class UiAmountToAmountParams(PydanticModel):
    """UiAmountToAmount token transaction params."""

    program_id: Pubkey
    """SPL Token program account."""
    mint: Pubkey
    """Mint to use for conversion."""
    ui_amount: str
    """The ui_amount string to convert."""
