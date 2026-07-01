"""SPL token instructions."""  # pylint: disable=too-many-lines

from __future__ import annotations

from typing import Any, List, Union
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

from solana.utils.validate import validate_instruction_keys, validate_instruction_type
from spl.token import models
from spl.token._layouts import (
    INSTRUCTIONS_LAYOUT,
    InstructionType,
    TransferFeeInstructionType,
)
from spl.token.constants import (
    ASSOCIATED_TOKEN_PROGRAM_ID,
    TOKEN_PROGRAM_ID,
    TOKEN_2022_PROGRAM_ID,
)

# Re-exported for backwards compatibility; the canonical definition now lives in spl.token.models.
from spl.token.models import AuthorityType


def __parse_and_validate_instruction(
    instruction: Instruction,
    expected_keys: int,
    expected_type: InstructionType,
) -> Any:  # Returns a Construct container.
    validate_instruction_keys(instruction, expected_keys)
    data = INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(data, expected_type)
    return data


def decode_initialize_mint(instruction: Instruction) -> models.InitializeMintParams:
    """Decode an initialize mint token instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.INITIALIZE_MINT)
    return models.InitializeMintParams(
        decimals=parsed_data.args.decimals,
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        mint_authority=Pubkey(parsed_data.args.mint_authority),
        freeze_authority=(
            Pubkey(parsed_data.args.freeze_authority) if parsed_data.args.freeze_authority_option else None
        ),
    )


def decode_initialize_mint2(instruction: Instruction) -> models.InitializeMint2Params:
    """Decode an initialize mint2 token instruction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.INITIALIZE_MINT2)
    return models.InitializeMint2Params(
        decimals=parsed_data.args.decimals,
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        mint_authority=Pubkey(parsed_data.args.mint_authority),
        freeze_authority=(
            Pubkey(parsed_data.args.freeze_authority) if parsed_data.args.freeze_authority_option else None
        ),
    )


def decode_initialize_account(
    instruction: Instruction,
) -> models.InitializeAccountParams:
    """Decode an initialize account token instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    _ = __parse_and_validate_instruction(instruction, 4, InstructionType.INITIALIZE_ACCOUNT)
    return models.InitializeAccountParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        owner=instruction.accounts[2].pubkey,
    )


def decode_initialize_account2(
    instruction: Instruction,
) -> models.InitializeAccount2Params:
    """Decode an initialize account2 token instruction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.INITIALIZE_ACCOUNT2)
    return models.InitializeAccount2Params(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        owner=Pubkey(parsed_data.args.owner),
    )


def decode_initialize_account3(
    instruction: Instruction,
) -> models.InitializeAccount3Params:
    """Decode an initialize account3 token instruction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.INITIALIZE_ACCOUNT3)
    return models.InitializeAccount3Params(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        owner=Pubkey(parsed_data.args.owner),
    )


def decode_initialize_multisig(
    instruction: Instruction,
) -> models.InitializeMultisigParams:
    """Decode an initialize multisig account token instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.INITIALIZE_MULTISIG)
    num_signers = parsed_data.args.m
    validate_instruction_keys(instruction, 2 + num_signers)
    return models.InitializeMultisigParams(
        program_id=instruction.program_id,
        multisig=instruction.accounts[0].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[-num_signers:]],
        m=num_signers,
    )


def decode_initialize_multisig2(
    instruction: Instruction,
) -> models.InitializeMultisig2Params:
    """Decode an initialize multisig2 account token instruction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.INITIALIZE_MULTISIG2)
    num_signers = parsed_data.args.m
    validate_instruction_keys(instruction, 1 + num_signers)
    signers: List[Pubkey] = [signer.pubkey for signer in instruction.accounts[-num_signers:]] if num_signers else []
    return models.InitializeMultisig2Params(
        program_id=instruction.program_id,
        multisig=instruction.accounts[0].pubkey,
        signers=signers,
        m=num_signers,
    )


def decode_transfer(instruction: Instruction) -> models.TransferParams:
    """Decode a transfer token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.TRANSFER)
    return models.TransferParams(
        program_id=instruction.program_id,
        source=instruction.accounts[0].pubkey,
        dest=instruction.accounts[1].pubkey,
        owner=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
        amount=parsed_data.args.amount,
    )


def decode_approve(instruction: Instruction) -> models.ApproveParams:
    """Decode a approve token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.APPROVE)
    return models.ApproveParams(
        program_id=instruction.program_id,
        source=instruction.accounts[0].pubkey,
        delegate=instruction.accounts[1].pubkey,
        owner=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
        amount=parsed_data.args.amount,
    )


def decode_revoke(instruction: Instruction) -> models.RevokeParams:
    """Decode a revoke token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    _ = __parse_and_validate_instruction(instruction, 2, InstructionType.REVOKE)
    return models.RevokeParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        owner=instruction.accounts[1].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[2:]],
    )


def decode_set_authority(instruction: Instruction) -> models.SetAuthorityParams:
    """Decode a set authority token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.SET_AUTHORITY)
    return models.SetAuthorityParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        authority=AuthorityType(parsed_data.args.authority_type),
        new_authority=(Pubkey(parsed_data.args.new_authority) if parsed_data.args.new_authority_option else None),
        current_authority=instruction.accounts[1].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[2:]],
    )


def decode_mint_to(instruction: Instruction) -> models.MintToParams:
    """Decode a mint to token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.MINT_TO)
    return models.MintToParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        mint=instruction.accounts[0].pubkey,
        dest=instruction.accounts[1].pubkey,
        mint_authority=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_burn(instruction: Instruction) -> models.BurnParams:
    """Decode a burn token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.BURN)
    return models.BurnParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        account=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        owner=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_close_account(instruction: Instruction) -> models.CloseAccountParams:
    """Decode a close account token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    _ = __parse_and_validate_instruction(instruction, 3, InstructionType.CLOSE_ACCOUNT)
    return models.CloseAccountParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        dest=instruction.accounts[1].pubkey,
        owner=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_freeze_account(instruction: Instruction) -> models.FreezeAccountParams:
    """Decode a freeze account token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    _ = __parse_and_validate_instruction(instruction, 3, InstructionType.FREEZE_ACCOUNT)
    return models.FreezeAccountParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        authority=instruction.accounts[2].pubkey,
        multi_signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_thaw_account(instruction: Instruction) -> models.ThawAccountParams:
    """Decode a thaw account token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    _ = __parse_and_validate_instruction(instruction, 3, InstructionType.THAW_ACCOUNT)
    return models.ThawAccountParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        authority=instruction.accounts[2].pubkey,
        multi_signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_transfer_checked(instruction: Instruction) -> models.TransferCheckedParams:
    """Decode a transfer_checked token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 4, InstructionType.TRANSFER2)
    return models.TransferCheckedParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        source=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        dest=instruction.accounts[2].pubkey,
        owner=instruction.accounts[3].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[4:]],
    )


def decode_approve_checked(instruction: Instruction) -> models.ApproveCheckedParams:
    """Decode a approve_checked token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 4, InstructionType.APPROVE2)
    return models.ApproveCheckedParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        source=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        delegate=instruction.accounts[2].pubkey,
        owner=instruction.accounts[3].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[4:]],
    )


def decode_mint_to_checked(instruction: Instruction) -> models.MintToCheckedParams:
    """Decode a mintTo2 token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.MINT_TO2)
    return models.MintToCheckedParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        mint=instruction.accounts[0].pubkey,
        dest=instruction.accounts[1].pubkey,
        mint_authority=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_burn_checked(instruction: Instruction) -> models.BurnCheckedParams:
    """Decode a burn_checked token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.BURN2)
    return models.BurnCheckedParams(
        program_id=instruction.program_id,
        amount=parsed_data.args.amount,
        decimals=parsed_data.args.decimals,
        account=instruction.accounts[0].pubkey,
        mint=instruction.accounts[1].pubkey,
        owner=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_sync_native(instruction: Instruction) -> models.SyncNativeParams:
    """Decode a burn_checked token transaction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction.
    """
    return models.SyncNativeParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
    )


def decode_get_account_data_size(
    instruction: Instruction,
) -> models.GetAccountDataSizeParams:
    """Decode a get_account_data_size token transaction and retrieve the instruction params."""
    _ = __parse_and_validate_instruction(instruction, 1, InstructionType.GET_ACCOUNT_DATA_SIZE)
    return models.GetAccountDataSizeParams(
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
    )


def decode_initialize_immutable_owner(
    instruction: Instruction,
) -> models.InitializeImmutableOwnerParams:
    """Decode an initialize_immutable_owner token transaction and retrieve the instruction params."""
    _ = __parse_and_validate_instruction(instruction, 1, InstructionType.INITIALIZE_IMMUTABLE_OWNER)
    return models.InitializeImmutableOwnerParams(
        program_id=instruction.program_id,
        account=instruction.accounts[0].pubkey,
    )


def decode_initialize_transfer_fee_config(
    instruction: Instruction,
) -> models.InitializeTransferFeeConfigParams:
    """Decode an initialize_transfer_fee_config token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.TRANSFER_FEE_EXTENSION)
    if parsed_data.args.transfer_fee_instruction_type != TransferFeeInstructionType.INITIALIZE_TRANSFER_FEE_CONFIG:
        raise ValueError("invalid transfer fee instruction type")
    args = parsed_data.args.args
    transfer_fee_config_authority = args.transfer_fee_config_authority
    withdraw_withheld_authority = args.withdraw_withheld_authority
    return models.InitializeTransferFeeConfigParams(
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        transfer_fee_config_authority=(
            Pubkey(transfer_fee_config_authority.pubkey) if transfer_fee_config_authority.option else None
        ),
        withdraw_withheld_authority=(
            Pubkey(withdraw_withheld_authority.pubkey) if withdraw_withheld_authority.option else None
        ),
        transfer_fee_basis_points=args.transfer_fee_basis_points,
        maximum_fee=args.maximum_fee,
    )


def decode_withdraw_withheld_tokens_from_accounts(
    instruction: Instruction,
) -> models.WithdrawWithheldTokensFromAccountsParams:
    """Decode a withdraw_withheld_tokens_from_accounts token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.TRANSFER_FEE_EXTENSION)
    if (
        parsed_data.args.transfer_fee_instruction_type
        != TransferFeeInstructionType.WITHDRAW_WITHHELD_TOKENS_FROM_ACCOUNTS
    ):
        raise ValueError("invalid transfer fee instruction type")
    num_token_accounts = parsed_data.args.args.num_token_accounts
    validate_instruction_keys(instruction, 3 + num_token_accounts)
    signers = instruction.accounts[3:-num_token_accounts] if num_token_accounts else instruction.accounts[3:]
    sources = instruction.accounts[-num_token_accounts:] if num_token_accounts else []
    return models.WithdrawWithheldTokensFromAccountsParams(
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        dest=instruction.accounts[1].pubkey,
        authority=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in signers],
        sources=[source.pubkey for source in sources],
    )


def decode_withdraw_withheld_tokens_from_mint(
    instruction: Instruction,
) -> models.WithdrawWithheldTokensFromMintParams:
    """Decode a withdraw_withheld_tokens_from_mint token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 3, InstructionType.TRANSFER_FEE_EXTENSION)
    if parsed_data.args.transfer_fee_instruction_type != TransferFeeInstructionType.WITHDRAW_WITHHELD_TOKENS_FROM_MINT:
        raise ValueError("invalid transfer fee instruction type")
    return models.WithdrawWithheldTokensFromMintParams(
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        dest=instruction.accounts[1].pubkey,
        authority=instruction.accounts[2].pubkey,
        signers=[signer.pubkey for signer in instruction.accounts[3:]],
    )


def decode_harvest_withheld_tokens_to_mint(
    instruction: Instruction,
) -> models.HarvestWithheldTokensToMintParams:
    """Decode a harvest_withheld_tokens_to_mint token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.TRANSFER_FEE_EXTENSION)
    if parsed_data.args.transfer_fee_instruction_type != TransferFeeInstructionType.HARVEST_WITHHELD_TOKENS_TO_MINT:
        raise ValueError("invalid transfer fee instruction type")
    return models.HarvestWithheldTokensToMintParams(
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        sources=[source.pubkey for source in instruction.accounts[1:]],
    )


def decode_amount_to_ui_amount(
    instruction: Instruction,
) -> models.AmountToUiAmountParams:
    """Decode an amount_to_ui_amount token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.AMOUNT_TO_UI_AMOUNT)
    return models.AmountToUiAmountParams(
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        amount=parsed_data.args.amount,
    )


def decode_ui_amount_to_amount(
    instruction: Instruction,
) -> models.UiAmountToAmountParams:
    """Decode a ui_amount_to_amount token transaction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.UI_AMOUNT_TO_AMOUNT)
    ui_amount_bytes: bytes = parsed_data.args.ui_amount
    return models.UiAmountToAmountParams(
        program_id=instruction.program_id,
        mint=instruction.accounts[0].pubkey,
        ui_amount=ui_amount_bytes.decode("utf-8"),
    )


def __add_signers(keys: List[AccountMeta], owner: Pubkey, signers: List[Pubkey]) -> None:
    if signers:
        keys.append(AccountMeta(pubkey=owner, is_signer=False, is_writable=False))
        for signer in signers:
            keys.append(AccountMeta(pubkey=signer, is_signer=True, is_writable=False))
    else:
        keys.append(AccountMeta(pubkey=owner, is_signer=True, is_writable=False))


def __burn_instruction(params: Union[models.BurnParams, models.BurnCheckedParams], data: Any) -> Instruction:
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def __sync_native_instruction(params: models.SyncNativeParams, data: Any) -> Instruction:
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
    ]

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def __freeze_or_thaw_instruction(
    params: Union[models.FreezeAccountParams, models.ThawAccountParams],
    instruction_type: InstructionType,
) -> Instruction:
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": instruction_type, "args": None})
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.authority, params.multi_signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def __mint_to_instruction(params: Union[models.MintToParams, models.MintToCheckedParams], data: Any) -> Instruction:
    keys = [
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.mint_authority, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def initialize_mint(params: models.InitializeMintParams) -> Instruction:
    """Creates a transaction instruction to initialize a new mint newly.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.

    Example:
        >>> from spl.token.models import InitializeMintParams
        >>> from spl.token.constants import TOKEN_PROGRAM_ID
        >>> from solders.pubkey import Pubkey
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i +1]) for i in range(4)]
        >>> mint_account, mint_authority, freeze_authority, owner = pubkeys
        >>> params = InitializeMintParams(
        ...     decimals=6,
        ...     freeze_authority=freeze_authority,
        ...     mint=mint_account,
        ...     mint_authority=mint_authority,
        ...     program_id=TOKEN_PROGRAM_ID,
        ... )
        >>> type(initialize_mint(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to initialize the mint.
    """
    freeze_authority, opt = (params.freeze_authority, 1) if params.freeze_authority else (Pubkey([0] * 31 + [0]), 0)
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.INITIALIZE_MINT,
            "args": {
                "decimals": params.decimals,
                "mint_authority": bytes(params.mint_authority),
                "freeze_authority_option": opt,
                "freeze_authority": bytes(freeze_authority),
            },
        }
    )
    return Instruction(
        accounts=[
            AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        ],
        program_id=params.program_id,
        data=data,
    )


def initialize_mint2(params: models.InitializeMint2Params) -> Instruction:
    """Creates a transaction instruction to initialize a new mint without providing the Rent sysvar."""
    freeze_authority, opt = (params.freeze_authority, 1) if params.freeze_authority else (Pubkey([0] * 31 + [0]), 0)
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.INITIALIZE_MINT2,
            "args": {
                "decimals": params.decimals,
                "mint_authority": bytes(params.mint_authority),
                "freeze_authority_option": opt,
                "freeze_authority": bytes(freeze_authority),
            },
        }
    )
    return Instruction(
        accounts=[
            AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
        ],
        program_id=params.program_id,
        data=data,
    )


def initialize_account(params: models.InitializeAccountParams) -> Instruction:
    """Creates a transaction instruction to initialize a new account to hold tokens.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.

    Example:
        >>> from spl.token.models import InitializeAccountParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> account, mint, owner, token = pubkeys
        >>> params = InitializeAccountParams(
        ...     account=account,
        ...     mint=mint,
        ...     owner=owner,
        ...     program_id=token,
        ... )
        >>> type(initialize_account(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to initialize the account.
    """
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.INITIALIZE_ACCOUNT, "args": None})
    return Instruction(
        accounts=[
            AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=params.owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        ],
        program_id=params.program_id,
        data=data,
    )


def initialize_account2(params: models.InitializeAccount2Params) -> Instruction:
    """Creates a transaction instruction to initialize a new account with owner passed in data."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.INITIALIZE_ACCOUNT2,
            "args": {"owner": bytes(params.owner)},
        }
    )
    return Instruction(
        accounts=[
            AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        ],
        program_id=params.program_id,
        data=data,
    )


def initialize_account3(params: models.InitializeAccount3Params) -> Instruction:
    """Creates a transaction instruction to initialize a new account with owner passed in data and no Rent sysvar."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.INITIALIZE_ACCOUNT3,
            "args": {"owner": bytes(params.owner)},
        }
    )
    return Instruction(
        accounts=[
            AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
        ],
        program_id=params.program_id,
        data=data,
    )


def initialize_multisig(params: models.InitializeMultisigParams) -> Instruction:
    """Creates a transaction instruction to initialize a multisignature account with N provided signers.

    This instruction requires no signers and MUST be included within the same Transaction as
    the system program's `CreateInstruction` that creates the account being initialized.
    Otherwise another party can acquire ownership of the uninitialized account.

    Example:
        >>> from spl.token.models import InitializeMultisigParams
        >>> m = 2   # Two signers
        >>> signers = [Pubkey([0] * 31 + [i]) for i in range(m)]
        >>> leading_zeros = [0] * 31
        >>> multisig_account, token = Pubkey(leading_zeros + [1]), Pubkey(leading_zeros + [2])
        >>> params = InitializeMultisigParams(
        ...     m=m,
        ...     multisig=multisig_account,
        ...     signers=signers,
        ...     program_id=token,
        ... )
        >>> type(initialize_multisig(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The instruction to initialize the multisig.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.INITIALIZE_MULTISIG,
            "args": {"m": params.m},
        }
    )
    keys = [
        AccountMeta(pubkey=params.multisig, is_signer=False, is_writable=True),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    for signer in params.signers:
        keys.append(AccountMeta(pubkey=signer, is_signer=False, is_writable=False))

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def initialize_multisig2(
    params: models.InitializeMultisig2Params,
) -> Instruction:
    """Creates a transaction instruction to initialize a multisignature account without providing the Rent sysvar."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.INITIALIZE_MULTISIG2,
            "args": {"m": params.m},
        }
    )
    keys = [
        AccountMeta(pubkey=params.multisig, is_signer=False, is_writable=True),
    ]
    for signer in params.signers:
        keys.append(AccountMeta(pubkey=signer, is_signer=False, is_writable=False))
    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def transfer(params: models.TransferParams) -> Instruction:
    """Creates a transaction instruction to transfers tokens from one account to another.

    Either directly or via a delegate.

    Example:
        >>> from spl.token.models import TransferParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> dest, owner, source, token = pubkeys
        >>> params = TransferParams(
        ...     amount=1000,
        ...     dest=dest,
        ...     owner=owner,
        ...     program_id=token,
        ...     source=source,
        ... )
        >>> type(transfer(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The transfer instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.TRANSFER,
            "args": {"amount": params.amount},
        }
    )
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def approve(params: models.ApproveParams) -> Instruction:
    """Creates a transaction instruction to approve a delegate.

    Example:
        >>> from spl.token.models import ApproveParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> delegate, owner, source, token = pubkeys
        >>> params = ApproveParams(
        ...     amount=123,
        ...     delegate=delegate,
        ...     owner=owner,
        ...     program_id=token,
        ...     source=source
        ... )
        >>> type(approve(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The approve instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.APPROVE, "args": {"amount": params.amount}})
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.delegate, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.owner, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def revoke(params: models.RevokeParams) -> Instruction:
    """Creates a transaction instruction that revokes delegate authority for a given account.

    Example:
        >>> from spl.token.models import RevokeParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(3)]
        >>> account, owner, token = pubkeys
        >>> params = RevokeParams(
        ...     account=account, owner=owner, program_id=token
        ... )
        >>> type(revoke(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The revoke instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.REVOKE, "args": None})
    keys = [AccountMeta(pubkey=params.account, is_signer=False, is_writable=True)]
    __add_signers(keys, params.owner, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def set_authority(params: models.SetAuthorityParams) -> Instruction:
    """Creates a transaction instruction to sets a new authority of a mint or account.

    Example:
        >>> from spl.token.models import SetAuthorityParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> account, current_authority, new_authority, token = pubkeys
        >>> params = SetAuthorityParams(
        ...     account=account,
        ...     authority=AuthorityType.ACCOUNT_OWNER,
        ...     current_authority=current_authority,
        ...     new_authority=new_authority,
        ...     program_id=token,
        ... )
        >>> type(set_authority(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The set authority instruction.
    """
    new_authority, opt = (params.new_authority, 1) if params.new_authority else (Pubkey([0] * 31 + [0]), 0)
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.SET_AUTHORITY,
            "args": {
                "authority_type": params.authority,
                "new_authority_option": opt,
                "new_authority": bytes(new_authority),
            },
        }
    )
    keys = [AccountMeta(pubkey=params.account, is_signer=False, is_writable=True)]
    __add_signers(keys, params.current_authority, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def mint_to(params: models.MintToParams) -> Instruction:
    """Creates a transaction instruction to mint new tokens to an account.

    The native mint does not support minting.

    Example:
        >>> from spl.token.models import MintToParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> dest, mint, mint_authority, token = pubkeys
        >>> params = MintToParams(
        ...     amount=123,
        ...     dest=dest,
        ...     mint=mint,
        ...     mint_authority=mint_authority,
        ...     program_id=token,
        ... )
        >>> type(mint_to(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The mint-to instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.MINT_TO, "args": {"amount": params.amount}})
    return __mint_to_instruction(params, data)


def burn(params: models.BurnParams) -> Instruction:
    """Creates a transaction instruction to burns tokens by removing them from an account.

    Example:
        >>> from spl.token.models import BurnParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> account, mint, owner, token = pubkeys
        >>> params = BurnParams(
        ...     amount=123, account=account, mint=mint, owner=owner, program_id=token,
        ... )
        >>> type(burn(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The burn instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.BURN, "args": {"amount": params.amount}})
    return __burn_instruction(params, data)


def close_account(params: models.CloseAccountParams) -> Instruction:
    """Creates a transaction instruction to close an account by transferring all its SOL to the destination account.

    Non-native accounts may only be closed if its token amount is zero.

    Example:
        >>> from spl.token.models import CloseAccountParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> account, dest, owner, token = pubkeys
        >>> params = CloseAccountParams(
        ...     account=account, dest=dest, owner=owner, program_id=token)
        >>> type(close_account(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The close-account instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.CLOSE_ACCOUNT, "args": None})
    keys = [
        AccountMeta(pubkey=params.account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def freeze_account(params: models.FreezeAccountParams) -> Instruction:
    """Creates a transaction instruction to freeze an initialized account using the mint's freeze_authority (if set).

    Example:
        >>> from spl.token.models import FreezeAccountParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> account, mint, authority, token = pubkeys
        >>> params = FreezeAccountParams(
        ...     account=account, mint=mint, authority=authority, program_id=token)
        >>> type(freeze_account(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The freeze-account instruction.
    """
    return __freeze_or_thaw_instruction(params, InstructionType.FREEZE_ACCOUNT)


def thaw_account(params: models.ThawAccountParams) -> Instruction:
    """Creates a transaction instruction to thaw a frozen account using the Mint's freeze_authority (if set).

    Example:
        >>> from spl.token.models import ThawAccountParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> account, mint, authority, token = pubkeys
        >>> params = ThawAccountParams(
        ...     account=account, mint=mint, authority=authority, program_id=token)
        >>> type(thaw_account(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The thaw-account instruction.
    """
    return __freeze_or_thaw_instruction(params, InstructionType.THAW_ACCOUNT)


def transfer_checked(params: models.TransferCheckedParams) -> Instruction:
    """This instruction differs from `transfer` in that the token mint and decimals value is asserted by the caller.

    Example:
        >>> from spl.token.models import TransferCheckedParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(5)]
        >>> dest, mint, owner, source, token = pubkeys
        >>> params = TransferCheckedParams(
        ...     amount=1000,
        ...     decimals=6,
        ...     dest=dest,
        ...     mint=mint,
        ...     owner=owner,
        ...     program_id=token,
        ...     source=source,
        ... )
        >>> type(transfer_checked(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The transfer-checked instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.TRANSFER2,
            "args": {"amount": params.amount, "decimals": params.decimals},
        }
    )
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.owner, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def approve_checked(params: models.ApproveCheckedParams) -> Instruction:
    """This instruction differs from `approve` in that the token mint and decimals value is asserted by the caller.

    Example:
        >>> from spl.token.models import ApproveCheckedParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(5)]
        >>> delegate, mint, owner, source, token = pubkeys
        >>> params = ApproveCheckedParams(
        ...     amount=1000,
        ...     decimals=6,
        ...     delegate=delegate,
        ...     mint=mint,
        ...     owner=owner,
        ...     program_id=token,
        ...     source=source,
        ... )
        >>> type(approve_checked(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The approve-checked instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.APPROVE2,
            "args": {"amount": params.amount, "decimals": params.decimals},
        }
    )
    keys = [
        AccountMeta(pubkey=params.source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=params.delegate, is_signer=False, is_writable=False),
    ]
    __add_signers(keys, params.owner, params.signers)

    return Instruction(accounts=keys, program_id=params.program_id, data=data)


def mint_to_checked(params: models.MintToCheckedParams) -> Instruction:
    """This instruction differs from `mint_to` in that the decimals value is asserted by the caller.

    Example:
        >>> from spl.token.models import MintToCheckedParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> dest, mint, mint_authority, token = pubkeys
        >>> params = MintToCheckedParams(
        ...     amount=123,
        ...     decimals=6,
        ...     dest=dest,
        ...     mint=mint,
        ...     mint_authority=mint_authority,
        ...     program_id=token,
        ... )
        >>> type(mint_to_checked(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The mint-to-checked instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.MINT_TO2,
            "args": {"amount": params.amount, "decimals": params.decimals},
        }
    )
    return __mint_to_instruction(params, data)


def burn_checked(params: models.BurnCheckedParams) -> Instruction:
    """This instruction differs from `burn` in that the decimals value is asserted by the caller.

    Example:
        >>> from spl.token.models import BurnCheckedParams
        >>> leading_zeros = [0] * 31
        >>> pubkeys = [Pubkey(leading_zeros + [i + 1]) for i in range(4)]
        >>> account, mint, owner, token = pubkeys
        >>> params = BurnCheckedParams(
        ...     amount=123, account=account, decimals=6, mint=mint, owner=owner, program_id=token,
        ... )
        >>> type(burn_checked(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The burn-checked instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.BURN2,
            "args": {"amount": params.amount, "decimals": params.decimals},
        }
    )
    return __burn_instruction(params, data)


def sync_native(params: models.SyncNativeParams) -> Instruction:
    """Syncs the amount field with the number of lamports of the account.

    Example:
        >>> from spl.token.models import SyncNativeParams
        >>> account = Pubkey.default()
        >>> params = SyncNativeParams(
        ...     program_id=TOKEN_PROGRAM_ID, account=account,
        ... )
        >>> type(sync_native(params))
        <class 'solders.instruction.Instruction'>

    Returns:
        The sync-native instruction.
    """
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.SYNC_NATIVE,
            "args": {},
        }
    )
    return __sync_native_instruction(params, data)


def get_account_data_size(
    params: models.GetAccountDataSizeParams,
) -> Instruction:
    """Gets the required size of an account for the given mint as a little-endian u64."""
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.GET_ACCOUNT_DATA_SIZE, "args": None})
    return Instruction(
        accounts=[AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False)],
        program_id=params.program_id,
        data=data,
    )


def initialize_immutable_owner(
    params: models.InitializeImmutableOwnerParams,
) -> Instruction:
    """Initializes the Immutable Owner extension for a token account."""
    data = INSTRUCTIONS_LAYOUT.build({"instruction_type": InstructionType.INITIALIZE_IMMUTABLE_OWNER, "args": None})
    return Instruction(
        accounts=[AccountMeta(pubkey=params.account, is_signer=False, is_writable=True)],
        program_id=params.program_id,
        data=data,
    )


def initialize_transfer_fee_config(
    params: models.InitializeTransferFeeConfigParams,
) -> Instruction:
    """Initializes the TransferFeeConfig extension for a mint."""
    transfer_fee_config_authority = (
        {"option": 1, "pubkey": bytes(params.transfer_fee_config_authority)}
        if params.transfer_fee_config_authority
        else {"option": 0, "pubkey": None}
    )
    withdraw_withheld_authority = (
        {"option": 1, "pubkey": bytes(params.withdraw_withheld_authority)}
        if params.withdraw_withheld_authority
        else {"option": 0, "pubkey": None}
    )
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.TRANSFER_FEE_EXTENSION,
            "args": {
                "transfer_fee_instruction_type": TransferFeeInstructionType.INITIALIZE_TRANSFER_FEE_CONFIG,
                "args": {
                    "transfer_fee_config_authority": transfer_fee_config_authority,
                    "withdraw_withheld_authority": withdraw_withheld_authority,
                    "transfer_fee_basis_points": params.transfer_fee_basis_points,
                    "maximum_fee": params.maximum_fee,
                },
            },
        }
    )
    return Instruction(
        accounts=[AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True)],
        program_id=params.program_id,
        data=data,
    )


def withdraw_withheld_tokens_from_accounts(
    params: models.WithdrawWithheldTokensFromAccountsParams,
) -> Instruction:
    """Withdraws withheld tokens from token accounts to a fee receiver account."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.TRANSFER_FEE_EXTENSION,
            "args": {
                "transfer_fee_instruction_type": TransferFeeInstructionType.WITHDRAW_WITHHELD_TOKENS_FROM_ACCOUNTS,
                "args": {"num_token_accounts": len(params.sources)},
            },
        }
    )
    keys = [
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.authority, params.signers)
    keys.extend(AccountMeta(pubkey=source, is_signer=False, is_writable=True) for source in params.sources)
    return Instruction(
        accounts=keys,
        program_id=params.program_id,
        data=data,
    )


def withdraw_withheld_tokens_from_mint(
    params: models.WithdrawWithheldTokensFromMintParams,
) -> Instruction:
    """Withdraws withheld tokens from a mint to a fee receiver account."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.TRANSFER_FEE_EXTENSION,
            "args": {
                "transfer_fee_instruction_type": TransferFeeInstructionType.WITHDRAW_WITHHELD_TOKENS_FROM_MINT,
                "args": None,
            },
        }
    )
    keys = [
        AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True),
        AccountMeta(pubkey=params.dest, is_signer=False, is_writable=True),
    ]
    __add_signers(keys, params.authority, params.signers)
    return Instruction(
        accounts=keys,
        program_id=params.program_id,
        data=data,
    )


def harvest_withheld_tokens_to_mint(
    params: models.HarvestWithheldTokensToMintParams,
) -> Instruction:
    """Harvests withheld tokens from token accounts to the mint."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.TRANSFER_FEE_EXTENSION,
            "args": {
                "transfer_fee_instruction_type": TransferFeeInstructionType.HARVEST_WITHHELD_TOKENS_TO_MINT,
                "args": None,
            },
        }
    )
    keys = [AccountMeta(pubkey=params.mint, is_signer=False, is_writable=True)]
    keys.extend(AccountMeta(pubkey=source, is_signer=False, is_writable=True) for source in params.sources)
    return Instruction(
        accounts=keys,
        program_id=params.program_id,
        data=data,
    )


def amount_to_ui_amount(params: models.AmountToUiAmountParams) -> Instruction:
    """Converts a raw token amount to a UiAmount string using the given mint."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.AMOUNT_TO_UI_AMOUNT,
            "args": {"amount": params.amount},
        }
    )
    return Instruction(
        accounts=[AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False)],
        program_id=params.program_id,
        data=data,
    )


def ui_amount_to_amount(params: models.UiAmountToAmountParams) -> Instruction:
    """Converts a UiAmount string to a raw u64 token amount using the given mint."""
    data = INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": InstructionType.UI_AMOUNT_TO_AMOUNT,
            "args": {"ui_amount": params.ui_amount.encode("utf-8")},
        }
    )
    return Instruction(
        accounts=[AccountMeta(pubkey=params.mint, is_signer=False, is_writable=False)],
        program_id=params.program_id,
        data=data,
    )

def get_associated_token_address(owner: Pubkey, mint: Pubkey, token_program_id: Pubkey = TOKEN_PROGRAM_ID) -> Pubkey:
    """Derives the associated token address for the given wallet address and token mint.

    .. note::
        **Parameter order differs from solana/web3.js.**

        In JavaScript, ``getAssociatedTokenAddressSync`` takes ``(mint, owner)``,
        but this function takes ``(owner, mint)`` — the **opposite order**.
        To avoid silent bugs when porting JS code to Python, use keyword arguments::

            # Safe usage — explicit and unambiguous
            ata = get_associated_token_address(owner=owner_pubkey, mint=mint_pubkey)

    Args:
        owner (Pubkey): Owner's wallet address.
        mint (Pubkey): The token mint address.
        token_program_id (Pubkey, optional): The token program ID. Must be either
            ``spl.token.constants.TOKEN_PROGRAM_ID`` or ``spl.token.constants.TOKEN_2022_PROGRAM_ID``
            (default is ``TOKEN_PROGRAM_ID``).

    Returns:
        The public key of the derived associated token address.

    Raises:
        ValueError: If an invalid ``token_program_id`` is provided.
    """
    if token_program_id not in [TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID]:
        raise ValueError("token_program_id must be one of TOKEN_PROGRAM_ID or TOKEN_2022_PROGRAM_ID.")
    key, _ = Pubkey.find_program_address(
        seeds=[bytes(owner), bytes(token_program_id), bytes(mint)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    return key


def create_associated_token_account(
    payer: Pubkey,
    owner: Pubkey,
    mint: Pubkey,
    token_program_id: Pubkey = TOKEN_PROGRAM_ID,
) -> Instruction:
    """Creates a transaction instruction to create an associated token account.

    Args:
        payer (Pubkey): Payer's wallet address.
        owner (Pubkey): Owner's wallet address.
        mint (Pubkey): The token mint address.
        token_program_id (Pubkey, optional): The token program ID. Must be either `spl.token.constants.TOKEN_PROGRAM_ID`
            or `spl.token.constants.TOKEN_2022_PROGRAM_ID` (default is `TOKEN_PROGRAM_ID`).

    Returns:
        The instruction to create the associated token account.

    Raises:
        ValueError: If an invalid `token_program_id` is provided.
    """
    if token_program_id not in [TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID]:
        raise ValueError("token_program_id must be one of TOKEN_PROGRAM_ID or TOKEN_2022_PROGRAM_ID.")
    associated_token_address = get_associated_token_address(owner, mint, token_program_id)
    return Instruction(
        accounts=[
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=associated_token_address, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=token_program_id, is_signer=False, is_writable=False),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        ],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
        data=bytes(0),
    )


def create_idempotent_associated_token_account(
    payer: Pubkey,
    owner: Pubkey,
    mint: Pubkey,
    token_program_id: Pubkey = TOKEN_PROGRAM_ID,
) -> Instruction:
    """Creates an associated token account for the given address/token mint if it not exists.

    Returns:
        The instruction to create the associated token account.
    """
    if token_program_id not in [TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID]:
        raise ValueError("token_program_id must be one of TOKEN_PROGRAM_ID or TOKEN_2022_PROGRAM_ID.")
    associated_token_address = get_associated_token_address(owner, mint, token_program_id)
    return Instruction(
        accounts=[
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=associated_token_address, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=token_program_id, is_signer=False, is_writable=False),
        ],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
        data=bytes([1]),
    )
