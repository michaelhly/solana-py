"""Library to interface with SPL tokens on Solana."""

from enum import IntEnum
from typing import List, NamedTuple, Optional

from solana.publickey import PublicKey
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, TransactionInstruction
from solana.utils.validate import validate_instruction_keys, validate_instruction_type
from spl.token._layouts import INSTRUCTIONS_LAYOUT, InstructionType  # type: ignore


class AuthorityType(IntEnum):
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

    decimals: int
    """Number of base 10 digits to the right of the decimal place."""
    program_id: PublicKey
    """SPL Token program account."""
    mint: PublicKey
    """Public key of the minter account."""
    mint_authority: PublicKey
    """The authority/multisignature to mint tokens."""
    freeze_authority: Optional[PublicKey] = None
    """The freeze authority/multisignature of the mint."""


class InitializeAccountParams(NamedTuple):
    """Initialize token account transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    account: PublicKey
    """Public key of the new account."""
    mint: PublicKey
    """Public key of the minter account."""
    owner: PublicKey
    """Owner of the new account."""


class InitializeMultisigParams(NamedTuple):
    """Initialize multisig token account transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    multisig: PublicKey
    """New multisig account address."""
    m: int
    """The number of signers (M) required to validate this multisignature account."""
    signers: List[PublicKey] = []
    """Addresses of multisig signers."""


class TransferParams(NamedTuple):
    """Transfer token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    source: PublicKey
    """Source account."""
    destination: PublicKey
    """Destination account."""
    owner: PublicKey
    """Owner of the source account."""
    amount: int
    """Number of tokens to transfer."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig."""


class ApproveParams(NamedTuple):
    """Approve token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    source: PublicKey
    """Source account."""
    delegate: PublicKey
    """Delegate account authorized to perform a transfer of tokens from the source account."""
    owner: PublicKey
    """Owner of the source account."""
    amount: int
    """Maximum number of tokens the delegate may transfer."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig."""


class RevokeParams(NamedTuple):
    """Revoke token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    delegate: PublicKey
    """Delegate account authorized to perform a transfer of tokens from the source account."""
    owner: PublicKey
    """Owner of the source account."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig."""


class SetAuthorityParams(NamedTuple):
    """Set token authority transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    account: PublicKey
    """Public key of the token account."""
    authority: AuthorityType
    """The type of authority to update."""
    current_authority: PublicKey
    """Current authority of the specified type."""
    signers: List[PublicKey] = []
    """Signing accounts if `current_authority` is a multiSig."""
    new_authority: Optional[PublicKey] = None
    """New authority of the account."""


class MintToParams(NamedTuple):
    """Mint token transaction params."""

    program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    account: PublicKey
    """"""
    owner: PublicKey
    """"""
    amount: int
    """"""
    signers: List[PublicKey] = []
    """"""


class BurnParams(NamedTuple):
    """Burn token transaction params."""

    program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    mint: PublicKey
    """"""
    authority: PublicKey
    """"""
    amount: int
    """"""
    signers: List[PublicKey] = []
    """"""


class CloseAccountParams(NamedTuple):
    """Close token account transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    account: PublicKey
    """Address of account to close."""
    destination: PublicKey
    """Address of account to receive the remaining balance of the closed account."""
    owner: PublicKey
    """Address of account owner."""
    signers: List[PublicKey] = []
    """Addresses of signing accounts if `owner` is a multiSig."""


class FreezeAccountParams(NamedTuple):
    """Freeze token account transaction params."""

    program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    mint: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey] = []
    """"""


class ThawAccountParams(NamedTuple):
    """Thaw token account transaction params."""

    program_id: PublicKey
    """"""
    account: PublicKey
    """"""
    mint: PublicKey
    """"""
    owner: PublicKey
    """"""
    signers: List[PublicKey] = []
    """"""


class Transfer2Params(NamedTuple):
    """Transfer2 token transaction params."""

    program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    source: PublicKey
    """"""
    destination: PublicKey
    """"""
    authority: PublicKey
    """"""
    amount: int
    """"""
    decimal: int
    """"""
    signers: List[PublicKey] = []
    """"""


class Approve2Params(NamedTuple):
    """Approve2 token transaction params."""

    program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    source: PublicKey
    """"""
    delegate: PublicKey
    """"""
    owner: PublicKey
    """"""
    amount: int
    """"""
    decimal: int
    """"""
    signers: List[PublicKey] = []
    """"""


class MintTo2Params(NamedTuple):
    """MintTo2 token transaction params."""

    program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    account: PublicKey
    """"""
    owner: PublicKey
    """"""
    amount: int
    """"""
    decimal: int
    """"""
    signers: List[PublicKey] = []
    """"""


class Burn2Params(NamedTuple):
    """Burn2 token transaction params."""

    program_id: PublicKey
    """"""
    mint: PublicKey
    """"""
    account: PublicKey
    """"""
    owner: PublicKey
    """"""
    amount: int
    """"""
    decimal: int
    """"""
    signers: List[PublicKey] = []
    """"""


def decode_initialize_mint(instruction: TransactionInstruction) -> InitializeMintParams:
    """Decode an initialize mint token instruction and retrieve the instruction params."""
    validate_instruction_keys(instruction, 2)

    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.InitializeMint)

    return InitializeMintParams(
        decimals=parsed_data.args.decimals,
        program_id=instruction.program_id,
        mint=instruction.keys[0].pubkey,
        mint_authority=PublicKey(parsed_data.args.mint_authority),
        freeze_authority=PublicKey(parsed_data.args.freeze_authority)
        if parsed_data.args.freeze_authority_option
        else None,
    )


def decode_initialize_account(instruction: TransactionInstruction) -> InitializeAccountParams:
    """Decode an initialize account token instruction and retrieve the instruction params."""
    validate_instruction_keys(instruction, 4)

    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.InitializeAccount)

    return InitializeAccountParams(
        program_id=instruction.program_id,
        account=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
    )


def decode_initialize_multisig(instruction: TransactionInstruction) -> InitializeMultisigParams:
    """Decode an initialize multisig account token instruction and retrieve the instruction params."""
    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.InitializeMultisig)
    num_signers = parsed_data.args.m
    validate_instruction_keys(instruction, 2 + num_signers)

    return InitializeMultisigParams(
        program_id=instruction.program_id,
        multisig=instruction.keys[0].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[-num_signers:]],
        m=num_signers,
    )


def decode_transfer(instruction: TransactionInstruction) -> TransferParams:
    """Decode a transfer token transaction and retrieve the instruction params."""
    validate_instruction_keys(instruction, 3)

    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.Transfer)

    return TransferParams(
        program_id=instruction.program_id,
        source=instruction.keys[0].pubkey,
        destination=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
        amount=parsed_data.args.amount,
    )


def decode_approve(instruction: TransactionInstruction) -> ApproveParams:
    """Decode a approve token transaction and retrieve the instruction params."""
    validate_instruction_keys(instruction, 3)

    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.Approve)

    return ApproveParams(
        program_id=instruction.program_id,
        source=instruction.keys[0].pubkey,
        delegate=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
        amount=parsed_data.args.amount,
    )


def decode_revoke(instruction: TransactionInstruction) -> RevokeParams:
    """Decode a revoke token transaction and retrieve the instruction params."""
    validate_instruction_keys(instruction, 2)

    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.Revoke)

    return RevokeParams(
        program_id=instruction.program_id,
        delegate=instruction.keys[0].pubkey,
        owner=instruction.keys[1].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[2:]],
    )


def decode_set_authority(instruction: TransactionInstruction) -> SetAuthorityParams:
    """Decode a set authority token transaction and retrieve the instruction params."""
    validate_instruction_keys(instruction, 2)

    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.SetAuthority)

    return SetAuthorityParams(
        program_id=instruction.program_id,
        account=instruction.keys[0].pubkey,
        authority=AuthorityType(parsed_data.args.authority_type),
        new_authority=PublicKey(parsed_data.args.new_authority) if parsed_data.args.new_authority_option else None,
        current_authority=instruction.keys[1].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[2:]],
    )


def decode_mint_to(instruction: TransactionInstruction) -> MintToParams:
    """Decode a mint to token transaction and retrieve the instruction params."""
    raise NotImplementedError("decode_mint_to not implemented")


def decode_burn(instruction: TransactionInstruction) -> BurnParams:
    """Decode a burn token transaction and retrieve the instruction params."""
    raise NotImplementedError("decode_burn not implemented")


def decode_close_account(instruction: TransactionInstruction) -> CloseAccountParams:
    """Decode a close account token transaction and retrieve the instruction params."""
    validate_instruction_keys(instruction, 3)

    parsed_data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(parsed_data, InstructionType.CloseAccount)

    return CloseAccountParams(
        program_id=instruction.program_id,
        account=instruction.keys[0].pubkey,
        destination=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def decode_thaw_account(instruction: TransactionInstruction) -> ThawAccountParams:
    """Decode a thaw account token transaction and retrieve the instruction params."""
    raise NotImplementedError("decode_thaw_account not implemented")


def decode_transfer2(instruction: TransactionInstruction) -> Transfer2Params:
    """Decode a transfer2 token transaction and retrieve the instruction params."""
    raise NotImplementedError("decode_transfer2 not implemented")


def decode_approve2(instruction: TransactionInstruction) -> Transfer2Params:
    """Decode a approve2 token transaction and retrieve the instruction params."""
    raise NotImplementedError("decode_approve2 not implemented")


def decode_mint_to2(instruction: TransactionInstruction) -> MintTo2Params:
    """Decode a mintTo2 token transaction and retrieve the instruction params."""
    raise NotImplementedError("decode_mint_to2 not implemented")


def decode_burn2(instruction: TransactionInstruction) -> MintTo2Params:
    """Decode a burn2 token transaction and retrieve the instruction params."""
    raise NotImplementedError("decode_burn2 not implemented")


def __add_signers(keys: List[AccountMeta], owner: PublicKey, signers: List[PublicKey]) -> None:
    if signers:
        keys.append(AccountMeta(pubkey=owner, is_signer=False, is_writable=False))
        for signer in signers:
            keys.append(AccountMeta(pubkey=signer, is_signer=True, is_writable=False))
    else:
        keys.append(AccountMeta(pubkey=owner, is_signer=True, is_writable=False))


def initialize_mint(params: InitializeMintParams) -> TransactionInstruction:
    """Generate a transaction instruction to initialize a new mint newly.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.
    """
    freeze_authority, opt = (params.freeze_authority, 1) if params.freeze_authority else (PublicKey(0), 0)
    data = INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.InitializeMint,
            args=dict(
                decimals=params.decimals,
                mint_authority=bytes(params.mint_authority),
                freeze_authority_option=opt,
                freeze_authority=bytes(freeze_authority),
            ),
        )
    )
    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
            AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        ],
        program_id=params.program_id,
        data=data,
    )


def initialize_account(params: InitializeAccountParams) -> TransactionInstruction:
    """Generate a transaction instruction to initialize a new account to hold tokens.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.InitializeAccount, args=None))
    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=params.owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        ],
        program_id=params.program_id,
        data=data,
    )


def initialize_multisig(params: InitializeMultisigParams) -> TransactionInstruction:
    """Generate a transaction instruction to initialize a multisignature account with N provided signers.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.InitializeMultisig, args=dict(m=params.m)))
    keys = [
        AccountMeta(pubkey=params.multisig, is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
    ]
    for signer in params.signers:
        keys.append(AccountMeta(pubkey=signer, is_signer=False, is_writable=False))

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def transfer(params: TransferParams) -> TransactionInstruction:
    """Generate a transaction instruction to transfers tokens from one account to another.

    Either directly or via a delegate.
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.Transfer, args=dict(amount=params.amount)))
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.destination, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def approve(params: ApproveParams) -> TransactionInstruction:
    """Generate a transaction instruction to approves a delegate."""
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.Approve, args=dict(amount=params.amount)))
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.delegate, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def revoke(params: RevokeParams) -> TransactionInstruction:
    """Generate a transaction instruction to revokes the delegate's authority."""
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.Revoke, args=None))
    keys = [AccountMeta(pubkey=params.delegate, is_signer=False, is_writable=False)]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def set_authority(params: SetAuthorityParams) -> TransactionInstruction:
    """Generate a transaction instruction to sets a new authority of a mint or account."""
    new_authority, opt = (params.new_authority, 1) if params.new_authority else (PublicKey(0), 0)
    data = INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.SetAuthority,
            args=dict(authority_type=params.authority, new_authority_option=opt, new_authority=bytes(new_authority)),
        )
    )
    keys = [AccountMeta(pubkey=params.account, is_signer=False, is_writable=True)]
    __add_signers(keys, params.current_authority, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def mint_to(params: MintToParams) -> TransactionInstruction:
    """Generate a transaction instruction to mints new tokens to an account. The native mint does not support minting."""
    raise NotImplementedError("mint_to not implemented")


def burn(params: BurnParams) -> TransactionInstruction:
    """Generate a transaction instruction to burns tokens by removing them from an account."""
    raise NotImplementedError("burn not implemented")


def close_account(params: CloseAccountParams) -> TransactionInstruction:
    """Generate a transaction instruction to close an account by transferring all its SOL to the destination account.

    Non-native accounts may only be closed if its token amount is zero.
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.CloseAccount, args=None))
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.destination, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def freeze_account(params: FreezeAccountParams) -> TransactionInstruction:
    """Generate a transaction instruction to freeze an initialized account using the mint's freeze_authority (if set)."""  # noqa: E501 # pylint: disable=line-too-long
    raise NotImplementedError("freeze_account not implemented")


def thaw_account(params: ThawAccountParams) -> TransactionInstruction:
    """Generate a transaction instruction to thaw a Frozen account using the Mint's freeze_authority (if set)."""
    raise NotImplementedError("thaw_account not implemented")


def transfer2(params: Transfer2Params) -> TransactionInstruction:
    """This instruction differs from `transfer` in that the token mint and decimals value is asserted by the caller."""
    raise NotImplementedError("transfer2 not implemented")


def approve2(params: Approve2Params) -> TransactionInstruction:
    """This instruction differs from `approve` in that the token mint and decimals value is asserted by the caller."""
    raise NotImplementedError("approve2 not implemented")


def mint_to2(params: MintTo2Params) -> TransactionInstruction:
    """This instruction differs from `mint_to` in that the decimals value is asserted by the caller."""
    raise NotImplementedError("mint_to2 not implemented")


def burn2(params: Burn2Params) -> TransactionInstruction:
    """This instruction differs from `burn` in that the decimals value is asserted by the caller."""
    raise NotImplementedError("burn2 not implemented")
