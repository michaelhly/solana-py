"""Library to interface with system programs."""
from __future__ import annotations

from typing import Any, NamedTuple, Union

from solana._layouts.system_instructions import SYSTEM_INSTRUCTIONS_LAYOUT, InstructionType
from solana.publickey import PublicKey
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
    >>> sender, reciever = PublicKey(1), PublicKey(2)
    >>> instruction = transfer(
    ...     TransferParams(from_pubkey=sender, to_pubkey=reciever, lamports=1000)
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


def decode_create_with_seed(instruction: TransactionInstruction) -> CreateAccountWithSeedParams:
    """Decode a create account with seed system instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_create_with_seed not implemented")


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
            AccountMeta(pubkey=params.new_account_pubkey, is_signer=False, is_writable=True),
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
    >>> sender, reciever = PublicKey(1), PublicKey(2)
    >>> instruction = transfer(
    ...     TransferParams(from_pubkey=sender, to_pubkey=reciever, lamports=1000)
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


def create_account_with_seed(params: CreateAccountWithSeedParams) -> TransactionInstruction:
    """Generate an instruction that creates a new account at an address."""
    raise NotImplementedError("create_account_with_seed not implemented")


def create_nonce_account(params: Union[CreateNonceAccountParams, CreateAccountWithSeedParams]) -> Transaction:
    """Generate a Transaction that creates a new Nonce account."""
    raise NotImplementedError("create_nonce_account_params not implemented")


def nonce_initialization(params: InitializeNonceParams) -> TransactionInstruction:
    """Generate an instruction to initialize a Nonce account."""
    raise NotImplementedError("nonce_initialization not implemented")


def nonce_advance(params: AdvanceNonceParams) -> TransactionInstruction:
    """Generate an instruction to advance the nonce in a Nonce account."""
    raise NotImplementedError("nonce advance not implemented")


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
