"""Library to interface with the system program."""
from __future__ import annotations

from typing import Any, NamedTuple, Union

from solana import sysvar, config
from solana._layouts.system_instructions import SYSTEM_INSTRUCTIONS_LAYOUT, InstructionType
from solana._layout.stake_instructions import STAKE_INSTRUCTIONS_LAYOUT, StakeInstructionType
from solana.publickey import PublicKey
from solana.staking import Authorized, Lockup
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from solana.utils.validate import validate_instruction_keys, validate_instruction_type

SYS_PROGRAM_ID: PublicKey = PublicKey("11111111111111111111111111111111")
"""Public key that identifies the System program."""


# Instruction Params
class CreateAccountParams(NamedTuple):
    """Create account system transaction params."""

    from_pubkey: PublicKey
    """"""
    new_account_pubkey: PublicKey
    """"""
    lamports: int
    """"""
    space: int
    """"""
    program_id: PublicKey
    """"""


class TransferParams(NamedTuple):
    """Transfer system transaction params."""

    from_pubkey: PublicKey
    """"""
    to_pubkey: PublicKey
    """"""
    lamports: int
    """"""


class AssignParams(NamedTuple):
    """Assign system transaction params."""

    account_pubkey: PublicKey
    """"""
    program_id: PublicKey
    """"""


class CreateAccountWithSeedParams(NamedTuple):
    """Create account with seed system transaction params."""

    from_pubkey: PublicKey
    """"""
    new_account_pubkey: PublicKey
    """"""
    base_pubkey: PublicKey
    """"""
    seed: str
    """"""
    lamports: int
    """"""
    space: int
    """"""
    program_id: PublicKey
    """"""


class CreateNonceAccountParams(NamedTuple):
    """Create nonce account system transaction params."""

    from_pubkey: PublicKey
    """"""
    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""
    lamports: int
    """"""


class CreateNonceAccountWithSeedParams(NamedTuple):
    """Create nonce account with seed system transaction params."""

    from_pubkey: PublicKey
    """"""
    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""
    lamports: int
    """"""
    base_pubkey: PublicKey
    """"""
    seed: str
    """"""


class InitializeNonceParams(NamedTuple):
    """Initialize nonce account system instruction params."""

    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""


class AdvanceNonceParams(NamedTuple):
    """Advance nonce account system instruction params."""

    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""


class WithdrawNonceParams(NamedTuple):
    """Withdraw nonce account system transaction params."""

    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""
    to_pubkey: PublicKey
    """"""
    lamports: int
    """"""


class AuthorizeNonceParams(NamedTuple):
    """Authorize nonce account system transaction params."""

    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""
    new_authorized_pubkey: PublicKey
    """"""


class AllocateParams(NamedTuple):
    """Allocate account with seed system transaction params."""

    account_pubkey: PublicKey
    """"""
    space: int
    """"""


class AllocateWithSeedParams(NamedTuple):
    """Allocate account with seed system transaction params."""

    account_pubkey: PublicKey
    """"""
    base_pubkey: PublicKey
    """"""
    seed: str
    """"""
    space: int
    """"""
    program_id: PublicKey
    """"""


class AssignWithSeedParams(NamedTuple):
    """Assign account with seed system transaction params."""

    account_pubkey: PublicKey
    """"""
    base_pubkey: PublicKey
    """"""
    seed: str
    """"""
    program_id: PublicKey
    """"""


class InitializeStakeParams(NamedTuple):
    """Initialize Staking params"""
    stake_pubkey: PublicKey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""


class CreateStakeAccountParams(NamedTuple):
    """Create stake account transaction params."""

    from_pubkey: PublicKey
    """"""
    stake_pubkey: PublicKey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""
    lamports: int
    """"""


class CreateStakeAccountWithSeedParams(NamedTuple):
    """Create stake account with seed transaction params."""

    from_pubkey: PublicKey
    """"""
    stake_pubkey: PublicKey
    """"""
    base_pubkey: PublicKey
    """"""
    seed: str
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""
    lamports: int
    """"""


class DelegateStakeParams(NamedTuple):
    """Create delegate stake account transaction params."""

    stake_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""
    vote_pubkey: PublicKey
    """"""


class CreateAccountAndDelegateStakeParams(NamedTuple):
    """Create and delegate a stake account transaction params"""

    from_pubkey: PublicKey
    """"""
    stake_pubkey: PublicKey
    """"""
    vote_pubkey: PublicKey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""
    lamports: int
    """"""


class CreateAccountWithSeedAndDelegateStakeParams(NamedTuple):
    """Create and delegate stake account with seed transaction params."""

    from_pubkey: PublicKey
    """"""
    stake_pubkey: PublicKey
    """"""
    base_pubkey: PublicKey
    """"""
    seed: str
    """"""
    vote_pubkey: PublicKey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""
    lamports: int
    """"""


class WithdrawStakeParams(NamedTuple):
    """Withdraw stake account params"""

    stake_pubkey: PublicKey
    """"""
    withdrawer_pubkey: PublicKey
    """"""
    to_pubkey: PublicKey
    """"""
    lamports: int
    """"""
    custodian_pubkey: PublicKey
    """"""

def withdraw_stake(params: WithdrawStakeParams) -> Transaction:

    data = STAKE_INSTRUCTIONS_LAYOUT.build(
        instruction_type=StakeInstructionType.WITHDRAW_STAKE_ACCOUNT,
        args=dict(
            lamports=params.lamports
        ),
    )

    withdraw_instruction = TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.stake_pubkey, is_signer=True, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def create_account_and_delegate_stake(params: Union[CreateAccountAndDelegateStakeParams, CreateAccountWithSeedAndDelegateStakeParams]) -> Transaction:
    """Generate a transaction to crate and delegate a stake account"""

    initialize_stake_instruction = initialize_stake(
        InitializeStakeParams(
            stake_pubkey=params.stake_pubkey,
            authorized=params.authorized,
            lockup=params.lockup,
        )
    )

    create_account_instruction = _create_stake_account_instruction(params=params)

    delegate_stake_instruction = delegate_stake(
        DelegateStakeParams(
            stake_pubkey=params.stake_pubkey,
            authorized_pubkey=params.authorized_pubkey,
            vote_pubkey=params.vote_pubkey,
        )
    )

    return Transaction(fee_payer=params.from_pubkey).add(create_account_instruction, initialize_stake_instruction)


def delegate_stake(params: DelegateStakeParams) -> TransactionInstruction:
    """Generate an instruction to delete a Stake account"""

    data = STAKE_INSTRUCTIONS_LAYOUT.build(
        instruction_type=StakeInstructionType.DELEGATE_STAKE_ACCOUNT,
        args={},
    )
    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.stake_pubkey, is_signer=True, is_writable=True),
            AccountMeta(pubkey=params.vote_pubkey, is_signer=False, is_writable=False),
            AccountMeta(pubkey=sysvar.SYSVAR_CLOCK_PUBKEY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=sysvar.SYSVAR_STAKE_HISTORY_PUBKEY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=config.CONFIG_STAKE_PUBKEY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=params.authorized_pubkey, is_signer=False, is_writable=False),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def initialize_stake(params: InitializeStakeParams) -> TransactionInstruction:
    """Generate an instruction to initialize a Stake account."""
    authorized = dict(
        staker=params.authorized.staker,
        withdrawer=params.authorized.withdrawer,
    )
    lockup = dict(
        unix_timestamp=params.lockup.unix_timestamp,
        epoch=params.lockup.epoch,
        custodian=params.lockup.custodian
    )
    data = STAKE_INSTRUCTIONS_LAYOUT.build(
        instruction_type=StakeInstructionType.INITIALIZE_STAKE_ACCOUNT,
        args=dict(
            authorized=authorized,
            lockup=lockup,
        )
    )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.stake_pubkey, is_signer=True, is_writable=True),
            AccountMeta(pubkey=sysvar.SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def _create_stake_account_instruction(params: Union[CreateStakeAccountParams, CreateStakeAccountWithSeedParams, CreateAccountAndDelegateStakeParams, CreateAccountWithSeedAndDelegateStakeParams]) -> TransactionInstruction:
    if isinstance(params, CreateStakeAccountParams) or isinstance(params, CreateAccountAndDelegateStakeParams):
        return create_account(
            CreateAccountParams(
                from_pubkey=params.from_pubkey,
                new_account_pubkey=params.stake_pubkey,
                lamports=params.lamports,
                space=80,  # derived from rust implementation
                program_id=SYS_PROGRAM_ID,
            )
        )
    return create_account_with_seed(
        CreateAccountWithSeedParams(
            from_pubkey=params.from_pubkey,
            new_account_pubkey=params.stake_pubkey,
            base_pubkey=params.base_pubkey,
            seed=params.seed,
            lamports=params.lamports,
            space=80,  # derived from rust implementation
            program_id=SYS_PROGRAM_ID,
        )
    )


def create_stake_account(params: Union[CreateStakeAccountParams, CreateStakeAccountWithSeedParams]) -> Transaction:
    """Generate a Transaction that creates a new Staking Account"""

    initialize_stake_instruction = initialize_stake(
        InitializeStakeParams(
            stake_pubkey=params.stake_pubkey,
            authorized=params.authorized,
            lockup=params.lockup,
        )
    )

    create_account_instruction = _create_stake_account_instruction(params=params)

    return Transaction(fee_payer=params.from_pubkey).add(create_account_instruction, initialize_stake_instruction)


def __check_program_id(program_id: PublicKey) -> None:
    if program_id != SYS_PROGRAM_ID:
        raise ValueError("invalid instruction: programId is not SystemProgram")


def __parse_and_validate_instruction(
    instruction: TransactionInstruction,
    expected_keys: int,
    expected_type: InstructionType,
) -> Any:  # Returns a Construct container.
    validate_instruction_keys(instruction, expected_keys)
    data = SYSTEM_INSTRUCTIONS_LAYOUT.parse(instruction.data)
    validate_instruction_type(data, expected_type)
    return data


def decode_create_account(instruction: TransactionInstruction) -> CreateAccountParams:
    """Decode a create account system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> from_account, new_account, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
    >>> instruction = create_account(
    ...     CreateAccountParams(
    ...         from_pubkey=from_account, new_account_pubkey=new_account,
    ...         lamports=1, space=1, program_id=program_id)
    ... )
    >>> decode_create_account(instruction)
    CreateAccountParams(from_pubkey=11111111111111111111111111111112, new_account_pubkey=11111111111111111111111111111113, lamports=1, space=1, program_id=11111111111111111111111111111114)
    """  # noqa: E501 # pylint: disable=line-too-long
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.CREATE_ACCOUNT)
    return CreateAccountParams(
        from_pubkey=instruction.keys[0].pubkey,
        new_account_pubkey=instruction.keys[1].pubkey,
        lamports=parsed_data.args.lamports,
        space=parsed_data.args.space,
        program_id=PublicKey(parsed_data.args.program_id),
    )


def decode_transfer(instruction: TransactionInstruction) -> TransferParams:
    """Decode a transfer system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> sender, receiver = PublicKey(1), PublicKey(2)
    >>> instruction = transfer(
    ...     TransferParams(from_pubkey=sender, to_pubkey=receiver, lamports=1000)
    ... )
    >>> decode_transfer(instruction)
    TransferParams(from_pubkey=11111111111111111111111111111112, to_pubkey=11111111111111111111111111111113, lamports=1000)
    """  # pylint: disable=line-too-long # noqa: E501
    parsed_data = __parse_and_validate_instruction(instruction, 2, InstructionType.TRANSFER)
    return TransferParams(
        from_pubkey=instruction.keys[0].pubkey, to_pubkey=instruction.keys[1].pubkey, lamports=parsed_data.args.lamports
    )


def decode_allocate(instruction: TransactionInstruction) -> AllocateParams:
    """Decode an allocate system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> allocator = PublicKey(1)
    >>> instruction = allocate(
    ...     AllocateParams(account_pubkey=allocator,space=65537)
    ... )
    >>> decode_allocate(instruction)
    AllocateParams(account_pubkey=11111111111111111111111111111112, space=65537)
    """  # pylint: disable=line-too-long # noqa: E501
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.ALLOCATE)
    return AllocateParams(account_pubkey=instruction.keys[0].pubkey, space=parsed_data.args.space)


def decode_allocate_with_seed(instruction: TransactionInstruction) -> AllocateWithSeedParams:
    """Decode an allocate with seed system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> allocator, base, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
    >>> instruction = allocate(
    ...     AllocateWithSeedParams(
    ...         account_pubkey=allocator,
    ...         base_pubkey=base,
    ...         seed={"length": 4, "chars": "gqln"},
    ...         space=65537,
    ...         program_id=program_id
    ...     )
    ... )
    >>> decode_allocate_with_seed(instruction)
    AllocateWithSeedParams(account_pubkey=11111111111111111111111111111112, base_pubkey=11111111111111111111111111111113, seed=Container(length=4, chars=u'gqln'), space=65537, program_id=11111111111111111111111111111114)
    """  # pylint: disable=line-too-long # noqa: E501
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.ALLOCATE_WITH_SEED)
    return AllocateWithSeedParams(
        account_pubkey=instruction.keys[0].pubkey,
        base_pubkey=PublicKey(parsed_data.args.base),
        seed=parsed_data.args.seed,
        space=parsed_data.args.space,
        program_id=PublicKey(parsed_data.args.program_id),
    )


def decode_assign(instruction: TransactionInstruction) -> AssignParams:
    """Decode an assign system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> account, program_id = PublicKey(1), PublicKey(2)
    >>> instruction = assign(
    ...     AssignParams(account_pubkey=account, program_id=program_id)
    ... )
    >>> decode_assign(instruction)
    AssignParams(account_pubkey=11111111111111111111111111111112, program_id=11111111111111111111111111111113)
    """
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.ASSIGN)
    return AssignParams(account_pubkey=instruction.keys[0].pubkey, program_id=PublicKey(parsed_data.args.program_id))


def decode_assign_with_seed(instruction: TransactionInstruction) -> AssignWithSeedParams:
    """Decode an assign system with seed instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_assign_with_seed not implemented")


def decode_create_account_with_seed(instruction: TransactionInstruction) -> CreateAccountWithSeedParams:
    """Decode a create account with seed system instruction and retrieve the instruction params."""
    parsed_data = __parse_and_validate_instruction(instruction, 1, InstructionType.CREATE_ACCOUNT_WITH_SEED)
    return CreateAccountWithSeedParams(
        from_pubkey=instruction.keys[0].pubkey,
        new_account_pubkey=instruction.keys[1].pubkey,
        base_pubkey=PublicKey(parsed_data.args.base),
        seed=parsed_data.args.seed,
        lamports=parsed_data.args.lamports,
        space=parsed_data.args.space,
        program_id=PublicKey(parsed_data.args.program_id),
    )


def decode_nonce_initialize(instruction: TransactionInstruction) -> InitializeNonceParams:
    """Decode a nonce initialize system instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_nonce_initialize not implemented")


def decode_nonce_advance(instruction: TransactionInstruction) -> AdvanceNonceParams:
    """Decode a nonce advance system instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_nonce_advance not implemented")


def decode_nonce_withdraw(instruction: TransactionInstruction) -> WithdrawNonceParams:
    """Decode a nonce withdraw system instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_nonce_withdraw not implemented")


def decode_nonce_authorize(instruction: TransactionInstruction) -> AuthorizeNonceParams:
    """Decode a nonce authorize system instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_nonce_authorize not implemented")


def create_account(params: CreateAccountParams) -> TransactionInstruction:
    """Generate an instruction that creates a new account.

    >>> from solana.publickey import PublicKey
    >>> from_account, new_account, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
    >>> instruction = create_account(
    ...     CreateAccountParams(
    ...         from_pubkey=from_account, new_account_pubkey=new_account,
    ...         lamports=1, space=1, program_id=program_id)
    ... )
    >>> type(instruction)
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.CREATE_ACCOUNT,
            args=dict(lamports=params.lamports, space=params.space, program_id=bytes(params.program_id)),
        )
    )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.from_pubkey, is_signer=True, is_writable=True),
            AccountMeta(pubkey=params.new_account_pubkey, is_signer=True, is_writable=True),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def assign(params: Union[AssignParams, AssignWithSeedParams]) -> TransactionInstruction:
    """Generate an instruction that assigns an account to a program.

    >>> from solana.publickey import PublicKey
    >>> account, program_id = PublicKey(1), PublicKey(2)
    >>> instruction = assign(
    ...     AssignParams(account_pubkey=account, program_id=program_id)
    ... )
    >>> type(instruction)
    <class 'solana.transaction.TransactionInstruction'>
    """
    if isinstance(params, AssignWithSeedParams):
        raise NotImplementedError("assign with key is not implemented")
    data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
        dict(instruction_type=InstructionType.ASSIGN, args=dict(program_id=bytes(params.program_id)))
    )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.account_pubkey, is_signer=True, is_writable=True),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def transfer(params: TransferParams) -> TransactionInstruction:
    """Generate an instruction that transfers lamports from one account to another.

    >>> from solana.publickey import PublicKey
    >>> sender, receiver = PublicKey(1), PublicKey(2)
    >>> instruction = transfer(
    ...     TransferParams(from_pubkey=sender, to_pubkey=receiver, lamports=1000)
    ... )
    >>> type(instruction)
    <class 'solana.transaction.TransactionInstruction'>
    """
    data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
        dict(instruction_type=InstructionType.TRANSFER, args=dict(lamports=params.lamports))
    )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.from_pubkey, is_signer=True, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def create_account_with_seed(
    params: CreateAccountWithSeedParams,
) -> TransactionInstruction:
    """Generate a instruction that creates a new account at an address generated with `from`, a seed, and programId."""
    data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.CREATE_ACCOUNT_WITH_SEED,
            args=dict(
                base=bytes(params.base_pubkey),
                seed=params.seed,
                lamports=params.lamports,
                space=params.space,
                program_id=bytes(params.program_id),
            ),
        )
    )

    keys = [
        AccountMeta(pubkey=params.from_pubkey, is_signer=True, is_writable=True),
        AccountMeta(pubkey=params.new_account_pubkey, is_signer=False, is_writable=True),
    ]

    if params.base_pubkey != params.from_pubkey:
        keys.append(AccountMeta(pubkey=params.base_pubkey, is_signer=True, is_writable=False))

    return TransactionInstruction(keys=keys, program_id=SYS_PROGRAM_ID, data=data)


def create_nonce_account(params: Union[CreateNonceAccountParams, CreateNonceAccountWithSeedParams]) -> Transaction:
    """Generate a Transaction that creates a new Nonce account."""
    if isinstance(params, CreateNonceAccountParams):
        create_account_instruction = create_account(
            CreateAccountParams(
                from_pubkey=params.from_pubkey,
                new_account_pubkey=params.nonce_pubkey,
                lamports=params.lamports,
                space=80,  # derived from rust implementation
                program_id=SYS_PROGRAM_ID,
            )
        )
    else:
        create_account_instruction = create_account_with_seed(
            CreateAccountWithSeedParams(
                from_pubkey=params.from_pubkey,
                new_account_pubkey=params.nonce_pubkey,
                base_pubkey=params.base_pubkey,
                seed=params.seed,
                lamports=params.lamports,
                space=80,  # derived from rust implementation
                program_id=SYS_PROGRAM_ID,
            )
        )

    initialize_nonce_instruction = nonce_initialization(
        InitializeNonceParams(
            nonce_pubkey=params.nonce_pubkey,
            authorized_pubkey=params.authorized_pubkey,
        )
    )

    return Transaction(fee_payer=params.from_pubkey).add(create_account_instruction, initialize_nonce_instruction)


def nonce_initialization(params: InitializeNonceParams) -> TransactionInstruction:
    """Generate an instruction to initialize a Nonce account."""
    data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.INITIALIZE_NONCE_ACCOUNT,
            args=dict(
                authorized=bytes(params.authorized_pubkey),
            ),
        )
    )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.nonce_pubkey, is_signer=True, is_writable=True),
            AccountMeta(pubkey=sysvar.SYSVAR_RECENT_BLOCKHASHES_PUBKEY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=sysvar.SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def nonce_advance(params: AdvanceNonceParams) -> TransactionInstruction:
    """Generate an instruction to advance the nonce in a Nonce account."""
    data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
        dict(
            instruction_type=InstructionType.ADVANCE_NONCE_ACCOUNT,
            args={},
        )
    )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.nonce_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=sysvar.SYSVAR_RECENT_BLOCKHASHES_PUBKEY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=params.authorized_pubkey, is_signer=True, is_writable=True),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )


def nonce_withdraw(params: WithdrawNonceParams) -> TransactionInstruction:
    """Generate an instruction that withdraws lamports from a Nonce account."""
    raise NotImplementedError("nonce_withdraw not implemented")


def nonce_authorize(params: AuthorizeNonceParams) -> TransactionInstruction:
    """Generate an instruction that authorizes a new PublicKey as the authority on a Nonce account."""
    raise NotImplementedError("nonce_authorize not implemented")


def allocate(params: Union[AllocateParams, AllocateWithSeedParams]) -> TransactionInstruction:
    """Generate an instruction that allocates space in an account without funding.

    >>> from solana.publickey import PublicKey
    >>> allocator = PublicKey(1)
    >>> instruction = allocate(
    ...     AllocateParams(account_pubkey=allocator, space=65537)
    ... )
    >>> type(instruction)
    <class 'solana.transaction.TransactionInstruction'>
    """
    if isinstance(params, AllocateWithSeedParams):
        data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
            dict(
                instruction_type=InstructionType.ALLOCATE_WITH_SEED,
                args=dict(
                    base=bytes(params.base_pubkey),
                    seed=params.seed,
                    space=params.space,
                    program_id=bytes(params.program_id),
                ),
            )
        )
    else:
        data = SYSTEM_INSTRUCTIONS_LAYOUT.build(
            dict(instruction_type=InstructionType.ALLOCATE, args=dict(space=params.space))
        )

    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=params.account_pubkey, is_signer=True, is_writable=True),
        ],
        program_id=SYS_PROGRAM_ID,
        data=data,
    )
