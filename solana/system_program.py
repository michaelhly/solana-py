"""Library to interface with system programs."""
from __future__ import annotations

from typing import List, NamedTuple, Union

from solana.instruction import InstructionLayout, decode_data, encode_data
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, Transaction, TransactionInstruction, verify_instruction_keys
from solana.utils.helpers import from_uint8_bytes

# Instruction Indices
_CREATE_IDX = 0
_ASSIGN_IDX = 1
_TRANSFER_IDX = 2
_CREATE_WITH_SEED_IDX = 3
_ADVANCE_NONCE_ACCOUNT_IDX = 4
_WITHDRAW_NONCE_ACCOUNT_IDX = 5
_INITIALZE_NONCE_ACCOUNT_IDX = 6
_AUTHORIZE_NONCE_ACCOUNT_IDX = 7
_ALLOCATE_IDX = 8
_ALLOCATE_WITH_SEED_IDX = 9
_ASSIGN_WITH_SEED_IDX = 10


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


SYSTEM_INSTRUCTION_LAYOUTS: List[InstructionLayout] = [
    InstructionLayout(idx=_CREATE_IDX, fmt="QQ32s"),
    InstructionLayout(idx=_ASSIGN_IDX, fmt="32s"),
    InstructionLayout(idx=_TRANSFER_IDX, fmt="Q"),
    InstructionLayout(idx=_CREATE_WITH_SEED_IDX, fmt="UNIMPLEMENTED"),
    InstructionLayout(idx=_ADVANCE_NONCE_ACCOUNT_IDX, fmt=""),
    InstructionLayout(idx=_WITHDRAW_NONCE_ACCOUNT_IDX, fmt="Q"),
    InstructionLayout(idx=_INITIALZE_NONCE_ACCOUNT_IDX, fmt="32s"),
    InstructionLayout(idx=_AUTHORIZE_NONCE_ACCOUNT_IDX, fmt="32s"),
    InstructionLayout(idx=_ALLOCATE_IDX, fmt="32s"),
    InstructionLayout(idx=_ALLOCATE_WITH_SEED_IDX, fmt="UNIMPLEMENTED"),
    InstructionLayout(idx=_ASSIGN_WITH_SEED_IDX, fmt="UNIMPLEMENTED"),
]


def __check_program_id(program_id: PublicKey) -> None:
    if program_id != sys_program_id():
        raise ValueError("invalid instruction: programId is not SystemProgram")


def decode_instruction_layout(instruction: TransactionInstruction) -> InstructionLayout:
    """Decode a system instruction and retrieve the instruction layout.

    >>> from solana.publickey import PublicKey
    >>> from_account, new_account, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
    >>> create_tx = create_account(
    ...     CreateAccountParams(
    ...         from_pubkey=from_account, new_account_pubkey=new_account,
    ...         lamports=1, space=1, program_id=program_id)
    ... )
    >>> decode_instruction_layout(create_tx.instructions[0])
    InstructionLayout(idx=0, fmt='QQ32s')
    """
    # Slice the first 4 bytes to get the type
    type_data = instruction.data[:4]
    type_idx = from_uint8_bytes(type_data)
    if 0 <= type_idx < len(SYSTEM_INSTRUCTION_LAYOUTS):
        return SYSTEM_INSTRUCTION_LAYOUTS[type_idx]
    raise ValueError("unknown transaction instruction")


def decode_create_account(instruction: TransactionInstruction) -> CreateAccountParams:
    """Decode a create account system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> from_account, new_account, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
    >>> create_tx = create_account(
    ...     CreateAccountParams(
    ...         from_pubkey=from_account, new_account_pubkey=new_account,
    ...         lamports=1, space=1, program_id=program_id)
    ... )
    >>> decode_create_account(create_tx.instructions[0])
    CreateAccountParams(from_pubkey=11111111111111111111111111111112, new_account_pubkey=11111111111111111111111111111113, lamports=1, space=1, program_id=11111111111111111111111111111114)
    """  # noqa: E501 # pylint: disable=line-too-long
    __check_program_id(instruction.program_id)
    verify_instruction_keys(instruction, 2)

    layout = SYSTEM_INSTRUCTION_LAYOUTS[_CREATE_IDX]
    _, lamports, space, program_id = decode_data(layout, instruction.data)

    return CreateAccountParams(
        from_pubkey=instruction.keys[0].pubkey,
        new_account_pubkey=instruction.keys[1].pubkey,
        lamports=lamports,
        space=space,
        program_id=PublicKey(program_id),
    )


def decode_transfer(instruction: TransactionInstruction) -> TransferParams:
    """Decode a transfer system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> sender, reciever = PublicKey(1), PublicKey(2)
    >>> transfer_tx = transfer(
    ...     TransferParams(from_pubkey=sender, to_pubkey=reciever, lamports=1000)
    ... )
    >>> decode_transfer(transfer_tx.instructions[0])
    TransferParams(from_pubkey=11111111111111111111111111111112, to_pubkey=11111111111111111111111111111113, lamports=1000)
    """  # pylint: disable=line-too-long # noqa: E501
    __check_program_id(instruction.program_id)
    verify_instruction_keys(instruction, 2)

    layout = SYSTEM_INSTRUCTION_LAYOUTS[_TRANSFER_IDX]
    data = decode_data(layout, instruction.data)

    return TransferParams(
        from_pubkey=instruction.keys[0].pubkey, to_pubkey=instruction.keys[1].pubkey, lamports=data[1]
    )


def decode_allocate(instruction: TransactionInstruction) -> AllocateParams:
    """Decode an allocate system instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_allocate not implemented")


def decode_allocate_with_seed(instruction: TransactionInstruction) -> AllocateWithSeedParams:
    """Decode an allocate with seed system instruction and retrieve the instruction params."""
    raise NotImplementedError("decode_allocate_with_seed not implemented")


def decode_assign(instruction: TransactionInstruction) -> AssignParams:
    """Decode an assign system instruction and retrieve the instruction params.

    >>> from solana.publickey import PublicKey
    >>> account, program_id = PublicKey(1), PublicKey(2)
    >>> create_tx = assign(
    ...     AssignParams(account_pubkey=account, program_id=program_id)
    ... )
    >>> decode_assign(create_tx.instructions[0])
    AssignParams(account_pubkey=11111111111111111111111111111112, program_id=11111111111111111111111111111113)
    """
    __check_program_id(instruction.program_id)
    verify_instruction_keys(instruction, 1)

    layout = SYSTEM_INSTRUCTION_LAYOUTS[_ASSIGN_IDX]
    _, program_id = decode_data(layout, instruction.data)

    return AssignParams(account_pubkey=instruction.keys[0].pubkey, program_id=PublicKey(program_id))


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


def sys_program_id() -> PublicKey:
    """Public key that identifies the System program."""
    return PublicKey("11111111111111111111111111111111")


def create_account(params: CreateAccountParams) -> Transaction:
    """Generate a Transaction that creates a new account.

    >>> from solana.publickey import PublicKey
    >>> from_account, new_account, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
    >>> create_tx = create_account(
    ...     CreateAccountParams(
    ...         from_pubkey=from_account, new_account_pubkey=new_account,
    ...         lamports=1, space=1, program_id=program_id)
    ... )
    >>> type(create_tx)
    <class 'solana.transaction.Transaction'>
    """
    layout = SYSTEM_INSTRUCTION_LAYOUTS[_CREATE_IDX]
    data = encode_data(layout, params.lamports, params.space, bytes(params.program_id))

    txn = Transaction()
    txn.add(
        TransactionInstruction(
            keys=[
                AccountMeta(pubkey=params.from_pubkey, is_signer=True, is_writable=True),
                AccountMeta(pubkey=params.new_account_pubkey, is_signer=False, is_writable=True),
            ],
            program_id=sys_program_id(),
            data=data,
        )
    )
    return txn


def assign(params: Union[AssignParams, AssignWithSeedParams]) -> Transaction:
    """Generate a Transaction that assigns an account to a program.

    >>> from solana.publickey import PublicKey
    >>> account, program_id = PublicKey(1), PublicKey(2)
    >>> assign_tx = assign(
    ...     AssignParams(account_pubkey=account, program_id=program_id)
    ... )
    >>> type(assign_tx)
    <class 'solana.transaction.Transaction'>
    """
    if isinstance(params, AssignWithSeedParams):
        raise NotImplementedError("assign with key is not implemented")
    else:
        data = encode_data(SYSTEM_INSTRUCTION_LAYOUTS[_ASSIGN_IDX], bytes(params.program_id))

    txn = Transaction()
    txn.add(
        TransactionInstruction(
            keys=[
                AccountMeta(pubkey=params.account_pubkey, is_signer=True, is_writable=True),
            ],
            program_id=sys_program_id(),
            data=data,
        )
    )
    return txn


def transfer(params: TransferParams) -> Transaction:
    """Generate a Transaction that transfers lamports from one account to another.

    >>> from solana.publickey import PublicKey
    >>> sender, reciever = PublicKey(1), PublicKey(2)
    >>> transfer_tx = transfer(
    ...     TransferParams(from_pubkey=sender, to_pubkey=reciever, lamports=1000)
    ... )
    >>> type(transfer_tx)
    <class 'solana.transaction.Transaction'>
    """
    layout = SYSTEM_INSTRUCTION_LAYOUTS[_TRANSFER_IDX]
    data = encode_data(layout, params.lamports)

    txn = Transaction()
    txn.add(
        TransactionInstruction(
            keys=[
                AccountMeta(pubkey=params.from_pubkey, is_signer=True, is_writable=True),
                AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            ],
            program_id=sys_program_id(),
            data=data,
        )
    )
    return txn


def create_account_with_seed(params: CreateAccountWithSeedParams) -> Transaction:
    """Generate a Transaction that creates a new account at an address."""
    raise NotImplementedError("create_account_with_seed not implemented")


def create_nonce_account(param: Union[CreateNonceAccountParams, CreateAccountWithSeedParams]) -> Transaction:
    """Generate a Transaction that creates a new Nonce account."""
    raise NotImplementedError("create_nonce_account_params not implemented")


def nonce_initialization(param: InitializeNonceParams) -> TransactionInstruction:
    """Generate an instruction to initialize a Nonce account."""
    raise NotImplementedError("nonce_initialization not implemented")


def nonce_advance(param: AdvanceNonceParams) -> TransactionInstruction:
    """Generate an instruction to advance the nonce in a Nonce account."""
    raise NotImplementedError("nonce advance not implemented")


def nonce_withdraw(param: WithdrawNonceParams) -> Transaction:
    """Generate a Transaction that withdraws lamports from a Nonce account."""
    raise NotImplementedError("nonce_withdraw not implemented")


def nonce_authorize(param: AuthorizeNonceParams) -> Transaction:
    """Generate a Transaction that authorizes a new PublicKey as the authority on a Nonce account."""
    raise NotImplementedError("nonce_authorize not implemented")


def allocate(param: Union[AllocateParams, AllocateWithSeedParams]) -> Transaction:
    """Generate a Transaction that allocates space in an account without funding."""
    raise NotImplementedError("allocate not implemented")
