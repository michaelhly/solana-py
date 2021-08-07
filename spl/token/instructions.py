"""SPL token instructions."""

from enum import IntEnum
from typing import Any, List, NamedTuple, Optional, Union

from solana.publickey import PublicKey
from solana.system_program import SYS_PROGRAM_ID
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.transaction import AccountMeta, TransactionInstruction
from solana.utils.validate import validate_instruction_keys, validate_instruction_type
from spl.token._layouts import INSTRUCTIONS_LAYOUT, InstructionType
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID


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
    dest: PublicKey
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
    """SPL Token program account."""
    mint: PublicKey
    """Public key of the minter account."""
    dest: PublicKey
    """Public key of the account to mint to."""
    mint_authority: PublicKey
    """The mint authority."""
    amount: int
    """Amount to mint."""
    signers: List[PublicKey] = []
    """Signing accounts if `mint_authority` is a multiSig."""


class BurnParams(NamedTuple):
    """Burn token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    account: PublicKey
    """Account to burn tokens from."""
    mint: PublicKey
    """Public key of the minter account."""
    owner: PublicKey
    """Owner of the account."""
    amount: int
    """Amount to burn."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig"""


class CloseAccountParams(NamedTuple):
    """Close token account transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    account: PublicKey
    """Address of account to close."""
    dest: PublicKey
    """Address of account to receive the remaining balance of the closed account."""
    owner: PublicKey
    """Owner of the account."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig"""


class FreezeAccountParams(NamedTuple):
    """Freeze token account transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    account: PublicKey
    """Account to freeze."""
    mint: PublicKey
    """Public key of the minter account."""
    owner: PublicKey
    """Owner of the account."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig"""


class ThawAccountParams(NamedTuple):
    """Thaw token account transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    account: PublicKey
    """Account to thaw."""
    mint: PublicKey
    """Public key of the minter account."""
    owner: PublicKey
    """Owner of the account."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig"""


class Transfer2Params(NamedTuple):
    """Transfer2 token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    source: PublicKey
    """Source account."""
    mint: PublicKey
    """Public key of the minter account."""
    dest: PublicKey
    """Destination account."""
    owner: PublicKey
    """Owner of the source account."""
    amount: int
    """Number of tokens to transfer."""
    decimals: int
    """Amount decimals."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig."""


class Approve2Params(NamedTuple):
    """Approve2 token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    source: PublicKey
    """Source account."""
    mint: PublicKey
    """Public key of the minter account."""
    delegate: PublicKey
    """Delegate account authorized to perform a transfer of tokens from the source account."""
    owner: PublicKey
    """Owner of the source account."""
    amount: int
    """Maximum number of tokens the delegate may transfer."""
    decimals: int
    """Amount decimals."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig."""


class MintTo2Params(NamedTuple):
    """MintTo2 token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    mint: PublicKey
    """Public key of the minter account."""
    dest: PublicKey
    """Public key of the account to mint to."""
    mint_authority: PublicKey
    """The mint authority."""
    amount: int
    """Amount to mint."""
    decimals: int
    """Amount decimals."""
    signers: List[PublicKey] = []
    """Signing accounts if `mint_authority` is a multiSig."""


class Burn2Params(NamedTuple):
    """Burn2 token transaction params."""

    program_id: PublicKey
    """SPL Token program account."""
    mint: PublicKey
    """Public key of the minter account."""
    account: PublicKey
    """Account to burn tokens from."""
    owner: PublicKey
    """Owner of the account."""
    amount: int
    """Amount to burn."""
    decimals: int
    """Amount decimals."""
    signers: List[PublicKey] = []
    """Signing accounts if `owner` is a multiSig"""


def __parse_and_validate_instruction(
    instruction: TransactionInstruction,
    expected_keys: int,
    expected_type: InstructionType,
) -> Any:  # Returns a Construct container.
    validate_instruction_keys(instruction, expected_keys)
    data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(data, expected_type)
    return data


def decode_initialize_mint(instruction: TransactionInstruction) -> InitializeMintParams:
    """Decode an initialize mint token instruction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.INITIALIZE_MINT)
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
    _ = __parse_and_validate_instruction(instruction, 4, InstructionType.INITIALIZE_ACCOUNT)
    return InitializeAccountParams(
        program_id=instruction.program_id,
        account=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
    )


def decode_initialize_multisig(instruction: TransactionInstruction) -> InitializeMultisigParams:
    """Decode an initialize multisig account token instruction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.INITIALIZE_MULTISIG)
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
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.TRANSFER)
    return TransferParams(
        program_id=instruction.program_id,
        source=instruction.keys[0].pubkey,
        dest=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
        amount=parsed_data.args.amount,
    )


def decode_approve(instruction: TransactionInstruction) -> ApproveParams:
    """Decode a approve token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.APPROVE)
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
    _ = __parse_and_validate_instruction(instruction, 2, InstructionType.REVOKE)
    return RevokeParams(
        program_id=instruction.program_id,
        delegate=instruction.keys[0].pubkey,
        owner=instruction.keys[1].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[2:]],
    )


def decode_set_authority(instruction: TransactionInstruction) -> SetAuthorityParams:
    """Decode a set authority token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.SET_AUTHORITY)
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
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.MINT_TO)
    return MintToParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        mint=instruction.keys[0].pubkey,
        dest=instruction.keys[1].pubkey,
        mint_authority=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def decode_burn(instruction: TransactionInstruction) -> BurnParams:
    """Decode a burn token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.BURN)
    return BurnParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        account=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def decode_close_account(instruction: TransactionInstruction) -> CloseAccountParams:
    """Decode a close account token transaction and retrieve the instruction params."""
    _ = __parse_and_validate_instruction(instruction, 3, InstructionType.CLOSE_ACCOUNT)
    return CloseAccountParams(
        program_id=instruction.program_id,
        account=instruction.keys[0].pubkey,
        dest=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def decode_freeze_account(instruction: TransactionInstruction) -> FreezeAccountParams:
    """Decode a freeze account token transaction and retrieve the instruction params."""
    _ = __parse_and_validate_instruction(instruction, 3, InstructionType.FREEZE_ACCOUNT)
    return FreezeAccountParams(
        program_id=instruction.program_id,
        account=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def decode_thaw_account(instruction: TransactionInstruction) -> ThawAccountParams:
    """Decode a thaw account token transaction and retrieve the instruction params."""
    _ = __parse_and_validate_instruction(instruction, 3, InstructionType.THAW_ACCOUNT)
    return ThawAccountParams(
        program_id=instruction.program_id,
        account=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def decode_transfer2(instruction: TransactionInstruction) -> Transfer2Params:
    """Decode a transfer2 token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 4, InstructionType.TRANSFER2)
    return Transfer2Params(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        source=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        dest=instruction.keys[2].pubkey,
        owner=instruction.keys[3].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[4:]],
    )


def decode_approve2(instruction: TransactionInstruction) -> Approve2Params:
    """Decode a approve2 token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 4, InstructionType.APPROVE2)
    return Approve2Params(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        source=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        delegate=instruction.keys[2].pubkey,
        owner=instruction.keys[3].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[4:]],
    )


def decode_mint_to2(instruction: TransactionInstruction) -> MintTo2Params:
    """Decode a mintTo2 token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.MINT_TO2)
    return MintTo2Params(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        mint=instruction.keys[0].pubkey,
        dest=instruction.keys[1].pubkey,
        mint_authority=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def decode_burn2(instruction: TransactionInstruction) -> Burn2Params:
    """Decode a burn2 token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.BURN2)
    return Burn2Params(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        account=instruction.keys[0].pubkey,
        mint=instruction.keys[1].pubkey,
        owner=instruction.keys[2].pubkey,
        signers=[signer.pubkey for signer in instruction.keys[3:]],
    )


def __add_signers(keys: List[AccountMeta], owner: PublicKey, signers: List[PublicKey]) -> None:
    if signers:
        keys.append(AccountMeta(pubkey=owner, is_signer=False, is_writable=False))
        for signer in signers:
            keys.append(AccountMeta(pubkey=signer, is_signer=True, is_writable=False))
    else:
        keys.append(AccountMeta(pubkey=owner, is_signer=True, is_writable=False))


def __burn_instruction(params: Union[BurnParams, Burn2Params], data: Any) -> TransactionInstruction:
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def __freeze_or_thaw_instruction(
    params: Union[FreezeAccountParams, ThawAccountParams], instruction_type: InstructionType
) -> TransactionInstruction:
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=instruction_type, args=None))
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def __mint_to_instruction(params: Union[MintToParams, MintTo2Params], data: Any) -> TransactionInstruction:
    keys = [
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.mint_authority, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def initialize_mint(params: InitializeMintParams) -> TransactionInstruction:
    """Creates a transaction instruction to initialize a new mint newly.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.

    >>> from spl.token.constants import TOKEN_PROGRAM_ID
    >>> mint_account, mint_authority, freeze_authority, owner = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = InitializeMintParams(
    ...     decimals=6,
    ...     freeze_authority=freeze_authority,
    ...     mint=mint_account,
    ...     mint_authority=mint_authority,
    ...     program_id=TOKEN_PROGRAM_ID,
    ... )
    >>> type(initialize_mint(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    freeze_authority, opt = (params.freeze_authority, 1) if params.freeze_authority else (PublicKey(0), 0)
    data = INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.INITIALIZE_MINT,
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
    """Creates a transaction instruction to initialize a new account to hold tokens.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.

    >>> account, mint, owner, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = InitializeAccountParams(
    ...     account=account,
    ...     mint=mint,
    ...     owner=owner,
    ...     program_id=token,
    ... )
    >>> type(initialize_account(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.INITIALIZE_ACCOUNT, args=None))
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
    """Creates a transaction instruction to initialize a multisignature account with N provided signers.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.

    >>> m = 2   # Two signers
    >>> signers = [PublicKey(i) for i in range(m)]
    >>> multisig_account, token = PublicKey(1), PublicKey(2)
    >>> params = InitializeMultisigParams(
    ...     m=m,
    ...     multisig=multisig_account,
    ...     signers=signers,
    ...     program_id=token,
    ... )
    >>> type(initialize_multisig(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.INITIALIZE_MULTISIG, args=dict(m=params.m)))
    keys = [
        AccountMeta(pubkey=params.multisig, is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
    ]
    for signer in params.signers:
        keys.append(AccountMeta(pubkey=signer, is_signer=False, is_writable=False))

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def transfer(params: TransferParams) -> TransactionInstruction:
    """Creates a transaction instruction to transfers tokens from one account to another.

    Either directly or via a delegate.

    >>> dest, owner, source, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = TransferParams(
    ...     amount=1000,
    ...     dest=dest,
    ...     owner=owner,
    ...     program_id=token,
    ...     source=source,
    ... )
    >>> type(transfer(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.TRANSFER, args=dict(amount=params.amount)))
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def approve(params: ApproveParams) -> TransactionInstruction:
    """Creates a transaction instruction to approves a delegate.

    >>> delegate, owner, source, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = ApproveParams(
    ...     amount=123,
    ...     delegate=delegate,
    ...     owner=owner,
    ...     program_id=token,
    ...     source=source
    ... )
    >>> type(approve(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.APPROVE, args=dict(amount=params.amount)))
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.delegate, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def revoke(params: RevokeParams) -> TransactionInstruction:
    """Creates a transaction instruction to revokes the delegate's authority.

    >>> delegate, owner, token = PublicKey(1), PublicKey(2), PublicKey(3)
    >>> params = RevokeParams(
    ...     delegate=delegate, owner=owner, program_id=token
    ... )
    >>> type(revoke(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.REVOKE, args=None))
    keys = [AccountMeta(pubkey=params.delegate, is_signer=False, is_writable=False)]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def set_authority(params: SetAuthorityParams) -> TransactionInstruction:
    """Creates a transaction instruction to sets a new authority of a mint or account.

    >>> account, current_authority, new_authority, token = (
    ...     PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    ... )
    >>> params = SetAuthorityParams(
    ...     account=account,
    ...     authority=AuthorityType.ACCOUNT_OWNER,
    ...     current_authority=current_authority,
    ...     new_authority=new_authority,
    ...     program_id=token,
    ... )
    >>> type(set_authority(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    new_authority, opt = (params.new_authority, 1) if params.new_authority else (PublicKey(0), 0)
    data = INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.SET_AUTHORITY,
            args=dict(authority_type=params.authority, new_authority_option=opt, new_authority=bytes(new_authority)),
        )
    )
    keys = [AccountMeta(pubkey=params.account, is_signer=False, is_writable=True)]
    __add_signers(keys, params.current_authority, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def mint_to(params: MintToParams) -> TransactionInstruction:
    """Creates a transaction instruction to mint new tokens to an account.

    The native mint does not support minting.

    >>> dest, mint, mint_authority, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = MintToParams(
    ...     amount=123,
    ...     dest=dest,
    ...     mint=mint,
    ...     mint_authority=mint_authority,
    ...     program_id=token,
    ... )
    >>> type(mint_to(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.MINT_TO, args=dict(amount=params.amount)))
    return __mint_to_instruction(params, data)


def burn(params: BurnParams) -> TransactionInstruction:
    """Creates a transaction instruction to burns tokens by removing them from an account.

    >>> account, mint, owner, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = BurnParams(
    ...     amount=123, account=account, mint=mint, owner=owner, program_id=token,
    ... )
    >>> type(burn(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.BURN, args=dict(amount=params.amount)))
    return __burn_instruction(params, data)


def close_account(params: CloseAccountParams) -> TransactionInstruction:
    """Creates a transaction instruction to close an account by transferring all its SOL to the destination account.

    Non-native accounts may only be closed if its token amount is zero.

    >>> account, dest, owner, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = CloseAccountParams(
    ...     account=account, dest=dest, owner=owner, program_id=token)
    >>> type(close_account(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(dict(instruction_type=InstructionType.CLOSE_ACCOUNT, args=None))
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def freeze_account(params: FreezeAccountParams) -> TransactionInstruction:
    """Creates a transaction instruction to freeze an initialized account using the mint's freeze_authority (if set).

    >>> account, mint, owner, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = FreezeAccountParams(
    ...     account=account, mint=mint, owner=owner, program_id=token)
    >>> type(freeze_account(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    return __freeze_or_thaw_instruction(params, InstructionType.FREEZE_ACCOUNT)


def thaw_account(params: ThawAccountParams) -> TransactionInstruction:
    """Creates a transaction instruction to thaw a frozen account using the Mint's freeze_authority (if set).

    >>> account, mint, owner, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = ThawAccountParams(
    ...     account=account, mint=mint, owner=owner, program_id=token)
    >>> type(thaw_account(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    return __freeze_or_thaw_instruction(params, InstructionType.THAW_ACCOUNT)


def transfer2(params: Transfer2Params) -> TransactionInstruction:
    """This instruction differs from `transfer` in that the token mint and decimals value is asserted by the caller.

    >>> dest, mint, owner, source, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4), PublicKey(5)
    >>> params = Transfer2Params(
    ...     amount=1000,
    ...     decimals=6,
    ...     dest=dest,
    ...     mint=mint,
    ...     owner=owner,
    ...     program_id=token,
    ...     source=source,
    ... )
    >>> type(transfer2(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(
        dict(instruction_type=InstructionType.TRANSFER2, args=dict(amount=params.amount, decimals=params.decimals))
    )
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def approve2(params: Approve2Params) -> TransactionInstruction:
    """This instruction differs from `approve` in that the token mint and decimals value is asserted by the caller.

    >>> delegate, mint, owner, source, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4), PublicKey(5)
    >>> params = Approve2Params(
    ...     amount=1000,
    ...     decimals=6,
    ...     delegate=delegate,
    ...     mint=mint,
    ...     owner=owner,
    ...     program_id=token,
    ...     source=source,
    ... )
    >>> type(approve2(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(
        dict(instruction_type=InstructionType.APPROVE2, args=dict(amount=params.amount, decimals=params.decimals))
    )
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=params.delegate, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.owner, params.signers)

    return TransactionInstruction(keys=keys, program_id=params.program_id, data=data)


def mint_to2(params: MintTo2Params) -> TransactionInstruction:
    """This instruction differs from `mint_to` in that the decimals value is asserted by the caller.

    >>> dest, mint, mint_authority, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = MintTo2Params(
    ...     amount=123,
    ...     decimals=6,
    ...     dest=dest,
    ...     mint=mint,
    ...     mint_authority=mint_authority,
    ...     program_id=token,
    ... )
    >>> type(mint_to2(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(
        dict(instruction_type=InstructionType.MINT_TO2, args=dict(amount=params.amount, decimals=params.decimals))
    )
    return __mint_to_instruction(params, data)


def burn2(params: Burn2Params) -> TransactionInstruction:
    """This instruction differs from `burn` in that the decimals value is asserted by the caller.

    >>> account, mint, owner, token = PublicKey(1), PublicKey(2), PublicKey(3), PublicKey(4)
    >>> params = Burn2Params(
    ...     amount=123, account=account, decimals=6, mint=mint, owner=owner, program_id=token,
    ... )
    >>> type(burn2(params))
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = INSTRUCTIONS_LAYOUT.build(
        dict(instruction_type=InstructionType.BURN2, args=dict(amount=params.amount, decimals=params.decimals))
    )
    return __burn_instruction(params, data)


def get_associated_token_address(owner: PublicKey, mint: PublicKey) -> PublicKey:
    """Derives the associated token address for the given wallet address and token mint."""
    key, _ = PublicKey.find_program_address(
        seeds=[bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)], program_id=ASSOCIATED_TOKEN_PROGRAM_ID
    )
    return key


def create_associated_token_account(payer: PublicKey, owner: PublicKey, mint: PublicKey) -> TransactionInstruction:
    """Creates a transaction instruction to create an associated token account."""
    associated_token_address = get_associated_token_address(owner, mint)
    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=associated_token_address, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        ],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
