"""Library to interface with the system program."""
from __future__ import annotations

from typing import NamedTuple, Union

from solders import system_program as ssp

from solana.publickey import PublicKey
from solana.transaction import Transaction, TransactionInstruction

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

    @classmethod
    def from_solders(cls, params: ssp.CreateAccountParams) -> CreateAccountParams:
        """Convert from `solders` CreateAccountParams.

        Args:
            params: `solders` CreateAccountParams

        Returns:
            `solana-py` CreateAccountParams
        """
        return cls(
            from_pubkey=PublicKey.from_solders(params["from_pubkey"]),
            new_account_pubkey=PublicKey.from_solders(params["to_pubkey"]),
            lamports=params["lamports"],
            space=params["space"],
            program_id=PublicKey.from_solders(params["owner"]),
        )

    def to_solders(self) -> ssp.CreateAccountParams:
        """Convert to `solders` CreateAccountParams.

        Returns:
            `solders` CreateAccountParams
        """
        return ssp.CreateAccountParams(
            from_pubkey=self.from_pubkey.to_solders(),
            to_pubkey=self.new_account_pubkey.to_solders(),
            lamports=self.lamports,
            space=self.space,
            owner=self.program_id.to_solders(),
        )


class TransferParams(NamedTuple):
    """Transfer system transaction params."""

    from_pubkey: PublicKey
    """"""
    to_pubkey: PublicKey
    """"""
    lamports: int
    """"""

    @classmethod
    def from_solders(cls, params: ssp.TransferParams) -> TransferParams:
        """Convert from `solders` TransferParams.

        Args:
            params: `solders` TransferParams

        Returns:
            `solana-py` TransferParams
        """
        return cls(
            from_pubkey=PublicKey.from_solders(params["from_pubkey"]),
            to_pubkey=PublicKey.from_solders(params["to_pubkey"]),
            lamports=params["lamports"],
        )

    def to_solders(self) -> ssp.TransferParams:
        """Convert to `solders` TransferParams.

        Returns:
            `solders` TransferParams
        """
        return ssp.TransferParams(
            from_pubkey=self.from_pubkey.to_solders(),
            to_pubkey=self.to_pubkey.to_solders(),
            lamports=self.lamports,
        )


class AssignParams(NamedTuple):
    """Assign system transaction params."""

    account_pubkey: PublicKey
    """"""
    program_id: PublicKey
    """"""

    @classmethod
    def from_solders(cls, params: ssp.AssignParams) -> AssignParams:
        """Convert from `solders` AssignParams.

        Args:
            params: `solders` AssignParams

        Returns:
            `solana-py` AssignParams
        """
        return cls(
            account_pubkey=PublicKey.from_solders(params["pubkey"]),
            program_id=PublicKey.from_solders(params["owner"]),
        )

    def to_solders(self) -> ssp.AssignParams:
        """Convert to `solders` AssignParams.

        Returns:
            `solders` AssignParams
        """
        return ssp.AssignParams(
            pubkey=self.account_pubkey.to_solders(),
            owner=self.program_id.to_solders(),
        )


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

    @classmethod
    def from_solders(cls, params: ssp.CreateAccountWithSeedParams) -> CreateAccountWithSeedParams:
        """Convert from `solders` CreateAccountWithSeedParams.

        Args:
            params: `solders` CreateAccountWithSeedParams

        Returns:
            `solana-py` CreateAccountWithSeedParams
        """
        return cls(
            from_pubkey=PublicKey.from_solders(params["from_pubkey"]),
            new_account_pubkey=PublicKey.from_solders(params["to_pubkey"]),
            base_pubkey=PublicKey.from_solders(params["base"]),
            seed=params["seed"],
            lamports=params["lamports"],
            space=params["space"],
            program_id=PublicKey.from_solders(params["owner"]),
        )

    def to_solders(self) -> ssp.CreateAccountWithSeedParams:
        """Convert to `solders` CreateAccountWithSeedParams.

        Returns:
            `solders` CreateAccountWithSeedParams
        """
        return ssp.CreateAccountWithSeedParams(
            from_pubkey=self.from_pubkey.to_solders(),
            to_pubkey=self.new_account_pubkey.to_solders(),
            base=self.base_pubkey.to_solders(),
            seed=self.seed,
            lamports=self.lamports,
            space=self.space,
            owner=self.program_id.to_solders(),
        )


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

    @classmethod
    def from_solders(cls, params: ssp.InitializeNonceAccountParams) -> InitializeNonceParams:
        """Convert from `solders` InitializeNonceParams.

        Args:
            params: `solders` InitializeNonceParams

        Returns:
            `solana-py` InitializeNonceParams
        """
        return cls(
            nonce_pubkey=PublicKey.from_solders(params["nonce_pubkey"]),
            authorized_pubkey=PublicKey.from_solders(params["authority"]),
        )

    def to_solders(self) -> ssp.InitializeNonceAccountParams:
        """Convert to `solders` InitializeNonceParams.

        Returns:
            `solders` InitializeNonceParams
        """
        return ssp.InitializeNonceAccountParams(
            nonce_pubkey=self.nonce_pubkey.to_solders(),
            authority=self.authorized_pubkey.to_solders(),
        )


class AdvanceNonceParams(NamedTuple):
    """Advance nonce account system instruction params."""

    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""

    @classmethod
    def from_solders(cls, params: ssp.AdvanceNonceAccountParams) -> AdvanceNonceParams:
        """Convert from `solders` AdvanceNonceParams.

        Args:
            params: `solders` AdvanceNonceParams

        Returns:
            `solana-py` AdvanceNonceParams
        """
        return cls(
            nonce_pubkey=PublicKey.from_solders(params["nonce_pubkey"]),
            authorized_pubkey=PublicKey.from_solders(params["authorized_pubkey"]),
        )

    def to_solders(self) -> ssp.AdvanceNonceAccountParams:
        """Convert to `solders` AdvanceNonceParams.

        Returns:
            `solders` AdvanceNonceParams
        """
        return ssp.AdvanceNonceAccountParams(
            nonce_pubkey=self.nonce_pubkey.to_solders(),
            authorized_pubkey=self.authorized_pubkey.to_solders(),
        )


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

    @classmethod
    def from_solders(cls, params: ssp.WithdrawNonceAccountParams) -> WithdrawNonceParams:
        """Convert from `solders` WithdrawNonceParams.

        Args:
            params: `solders` WithdrawNonceParams

        Returns:
            `solana-py` WithdrawNonceParams
        """
        return cls(
            nonce_pubkey=PublicKey.from_solders(params["nonce_pubkey"]),
            authorized_pubkey=PublicKey.from_solders(params["authorized_pubkey"]),
            to_pubkey=PublicKey.from_solders(params["to_pubkey"]),
            lamports=params["lamports"],
        )

    def to_solders(self) -> ssp.WithdrawNonceAccountParams:
        """Convert to `solders` WithdrawNonceParams.

        Returns:
            `solders` WithdrawNonceParams
        """
        return ssp.WithdrawNonceAccountParams(
            nonce_pubkey=self.nonce_pubkey.to_solders(),
            authorized_pubkey=self.authorized_pubkey.to_solders(),
            to_pubkey=self.to_pubkey.to_solders(),
            lamports=self.lamports,
        )


class AuthorizeNonceParams(NamedTuple):
    """Authorize nonce account system transaction params."""

    nonce_pubkey: PublicKey
    """"""
    authorized_pubkey: PublicKey
    """"""
    new_authorized_pubkey: PublicKey
    """"""

    @classmethod
    def from_solders(cls, params: ssp.AuthorizeNonceAccountParams) -> AuthorizeNonceParams:
        """Convert from `solders` AuthorizeNonceParams.

        Args:
            params: `solders` AuthorizeNonceParams

        Returns:
            `solana-py` AuthorizeNonceParams
        """
        return cls(
            nonce_pubkey=PublicKey.from_solders(params["nonce_pubkey"]),
            authorized_pubkey=PublicKey.from_solders(params["authorized_pubkey"]),
            new_authorized_pubkey=PublicKey.from_solders(params["new_authority"]),
        )

    def to_solders(self) -> ssp.AuthorizeNonceAccountParams:
        """Convert to `solders` AuthorizeNonceParams.

        Returns:
            `solders` AuthorizeNonceParams
        """
        return ssp.AuthorizeNonceAccountParams(
            nonce_pubkey=self.nonce_pubkey.to_solders(),
            authorized_pubkey=self.authorized_pubkey.to_solders(),
            new_authority=self.new_authorized_pubkey.to_solders(),
        )


class AllocateParams(NamedTuple):
    """Allocate account with seed system transaction params."""

    account_pubkey: PublicKey
    """"""
    space: int
    """"""

    @classmethod
    def from_solders(cls, params: ssp.AllocateParams) -> AllocateParams:
        """Convert from `solders` AllocateParams.

        Args:
            params: `solders` AllocateParams

        Returns:
            `solana-py` AllocateParams
        """
        return cls(
            account_pubkey=PublicKey.from_solders(params["pubkey"]),
            space=params["space"],
        )

    def to_solders(self) -> ssp.AllocateParams:
        """Convert to `solders` AllocateParams.

        Returns:
            `solders` AllocateParams
        """
        return ssp.AllocateParams(
            pubkey=self.account_pubkey.to_solders(),
            space=self.space,
        )


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

    @classmethod
    def from_solders(cls, params: ssp.AllocateWithSeedParams) -> AllocateWithSeedParams:
        """Convert from `solders` AllocateWithSeedParams.

        Args:
            params: `solders` AllocateWithSeedParams

        Returns:
            `solana-py` AllocateWithSeedParams
        """
        return cls(
            account_pubkey=PublicKey.from_solders(params["address"]),
            base_pubkey=PublicKey.from_solders(params["base"]),
            seed=params["seed"],
            space=params["space"],
            program_id=PublicKey.from_solders(params["owner"]),
        )

    def to_solders(self) -> ssp.AllocateWithSeedParams:
        """Convert to `solders` AllocateWithSeedParams.

        Returns:
            `solders` AllocateWithSeedParams
        """
        return ssp.AllocateWithSeedParams(
            address=self.account_pubkey.to_solders(),
            base=self.base_pubkey.to_solders(),
            seed=self.seed,
            space=self.space,
            owner=self.program_id.to_solders(),
        )


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

    @classmethod
    def from_solders(cls, params: ssp.AssignWithSeedParams) -> AssignWithSeedParams:
        """Convert from `solders` AssignWithSeedParams.

        Args:
            params: `solders` AssignWithSeedParams

        Returns:
            `solana-py` AssignWithSeedParams
        """
        return cls(
            account_pubkey=PublicKey.from_solders(params["address"]),
            base_pubkey=PublicKey.from_solders(params["base"]),
            seed=params["seed"],
            program_id=PublicKey.from_solders(params["owner"]),
        )

    def to_solders(self) -> ssp.AssignWithSeedParams:
        """Convert to `solders` AssignWithSeedParams.

        Returns:
            `solders` AssignWithSeedParams
        """
        return ssp.AssignWithSeedParams(
            address=self.account_pubkey.to_solders(),
            base=self.base_pubkey.to_solders(),
            seed=self.seed,
            owner=self.program_id.to_solders(),
        )


def decode_create_account(instruction: TransactionInstruction) -> CreateAccountParams:
    """Decode a create account system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Example:

        >>> from solana.publickey import PublicKey
        >>> from_account, new_account, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
        >>> instruction = create_account(
        ...     CreateAccountParams(
        ...         from_pubkey=from_account, new_account_pubkey=new_account,
        ...         lamports=1, space=1, program_id=program_id)
        ... )
        >>> decode_create_account(instruction)
        CreateAccountParams(from_pubkey=11111111111111111111111111111112, new_account_pubkey=11111111111111111111111111111113, lamports=1, space=1, program_id=11111111111111111111111111111114)

    Returns:
        The decoded instruction params.
    """  # noqa: E501 # pylint: disable=line-too-long
    return CreateAccountParams.from_solders(ssp.decode_create_account(instruction.to_solders()))


def decode_transfer(instruction: TransactionInstruction) -> TransferParams:
    """Decode a transfer system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Example:

        >>> from solana.publickey import PublicKey
        >>> sender, receiver = PublicKey(1), PublicKey(2)
        >>> instruction = transfer(
        ...     TransferParams(from_pubkey=sender, to_pubkey=receiver, lamports=1000)
        ... )
        >>> decode_transfer(instruction)
        TransferParams(from_pubkey=11111111111111111111111111111112, to_pubkey=11111111111111111111111111111113, lamports=1000)

    Returns:
        The decoded instruction params.
    """  # pylint: disable=line-too-long # noqa: E501
    return TransferParams.from_solders(ssp.decode_transfer(instruction.to_solders()))


def decode_allocate(instruction: TransactionInstruction) -> AllocateParams:
    """Decode an allocate system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Example:

        >>> from solana.publickey import PublicKey
        >>> allocator = PublicKey(1)
        >>> instruction = allocate(
        ...     AllocateParams(account_pubkey=allocator,space=65537)
        ... )
        >>> decode_allocate(instruction)
        AllocateParams(account_pubkey=11111111111111111111111111111112, space=65537)

    Returns:
        The decoded instruction params.
    """  # pylint: disable=line-too-long # noqa: E501
    return AllocateParams.from_solders(ssp.decode_allocate(instruction.to_solders()))


def decode_allocate_with_seed(instruction: TransactionInstruction) -> AllocateWithSeedParams:
    """Decode an allocate with seed system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Example:

        >>> from solana.publickey import PublicKey
        >>> allocator, base, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
        >>> instruction = allocate(
        ...     AllocateWithSeedParams(
        ...         account_pubkey=allocator,
        ...         base_pubkey=base,
        ...         seed="gqln",
        ...         space=65537,
        ...         program_id=program_id
        ...     )
        ... )
        >>> decode_allocate_with_seed(instruction)
        AllocateWithSeedParams(account_pubkey=11111111111111111111111111111112, base_pubkey=11111111111111111111111111111113, seed='gqln', space=65537, program_id=11111111111111111111111111111114)

    Returns:
        The decoded instruction params.
    """  # pylint: disable=line-too-long # noqa: E501
    return AllocateWithSeedParams.from_solders(ssp.decode_allocate_with_seed(instruction.to_solders()))


def decode_assign(instruction: TransactionInstruction) -> AssignParams:
    """Decode an assign system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Example:

        >>> from solana.publickey import PublicKey
        >>> account, program_id = PublicKey(1), PublicKey(2)
        >>> instruction = assign(
        ...     AssignParams(account_pubkey=account, program_id=program_id)
        ... )
        >>> decode_assign(instruction)
        AssignParams(account_pubkey=11111111111111111111111111111112, program_id=11111111111111111111111111111113)

    Returns:
        The decoded instruction params.
    """
    return AssignParams.from_solders(ssp.decode_assign(instruction.to_solders()))


def decode_assign_with_seed(instruction: TransactionInstruction) -> AssignWithSeedParams:
    """Decode an assign system with seed instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction params.
    """
    return AssignWithSeedParams.from_solders(ssp.decode_assign_with_seed(instruction.to_solders()))


def decode_create_account_with_seed(instruction: TransactionInstruction) -> CreateAccountWithSeedParams:
    """Decode a create account with seed system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction params.
    """
    return CreateAccountWithSeedParams.from_solders(ssp.decode_create_account_with_seed(instruction.to_solders()))


def decode_nonce_initialize(instruction: TransactionInstruction) -> InitializeNonceParams:
    """Decode a nonce initialize system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction params.
    """
    return InitializeNonceParams.from_solders(ssp.decode_initialize_nonce_account(instruction.to_solders()))


def decode_nonce_advance(instruction: TransactionInstruction) -> AdvanceNonceParams:
    """Decode a nonce advance system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction params.
    """
    return AdvanceNonceParams.from_solders(ssp.decode_advance_nonce_account(instruction.to_solders()))


def decode_nonce_withdraw(instruction: TransactionInstruction) -> WithdrawNonceParams:
    """Decode a nonce withdraw system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction params.
    """
    return WithdrawNonceParams.from_solders(ssp.decode_withdraw_nonce_account(instruction.to_solders()))


def decode_nonce_authorize(instruction: TransactionInstruction) -> AuthorizeNonceParams:
    """Decode a nonce authorize system instruction and retrieve the instruction params.

    Args:
        instruction: The instruction to decode.

    Returns:
        The decoded instruction params.

    """
    return AuthorizeNonceParams.from_solders(ssp.decode_authorize_nonce_account(instruction.to_solders()))


def create_account(params: CreateAccountParams) -> TransactionInstruction:
    """Generate an instruction that creates a new account.

    Args:
        params: The create account params.

    Example:
        >>> from solana.publickey import PublicKey
        >>> from_account, new_account, program_id = PublicKey(1), PublicKey(2), PublicKey(3)
        >>> instruction = create_account(
        ...     CreateAccountParams(
        ...         from_pubkey=from_account, new_account_pubkey=new_account,
        ...         lamports=1, space=1, program_id=program_id)
        ... )
        >>> type(instruction)
        <class 'solana.transaction.TransactionInstruction'>

    Returns:
        The instruction to create the account.
    """
    return TransactionInstruction.from_solders(ssp.create_account(params.to_solders()))


def assign(params: Union[AssignParams, AssignWithSeedParams]) -> TransactionInstruction:
    """Generate an instruction that assigns an account to a program.

    Args:
        params: The assign params.

    Example:
        >>> from solana.publickey import PublicKey
        >>> account, program_id = PublicKey(1), PublicKey(2)
        >>> instruction = assign(
        ...     AssignParams(account_pubkey=account, program_id=program_id)
        ... )
        >>> type(instruction)
        <class 'solana.transaction.TransactionInstruction'>
    """
    solders_ix = (
        ssp.assign(params.to_solders())
        if isinstance(params, AssignParams)
        else ssp.assign_with_seed(params.to_solders())
    )
    return TransactionInstruction.from_solders(solders_ix)


def transfer(params: TransferParams) -> TransactionInstruction:
    """Generate an instruction that transfers lamports from one account to another.

    Args:
        params: The transfer params.

    Example:

        >>> from solana.publickey import PublicKey
        >>> sender, receiver = PublicKey(1), PublicKey(2)
        >>> instruction = transfer(
        ...     TransferParams(from_pubkey=sender, to_pubkey=receiver, lamports=1000)
        ... )
        >>> type(instruction)
        <class 'solana.transaction.TransactionInstruction'>

    Returns:
        The transfer instruction.

    """
    return TransactionInstruction.from_solders(ssp.transfer(params.to_solders()))


def create_account_with_seed(
    params: CreateAccountWithSeedParams,
) -> TransactionInstruction:
    """Generate a instruction that creates a new account at an address generated with `from`, a seed, and programId.

    Args:
        params: account creation params.

    Returns:
        The instruction to create the account.
    """
    return TransactionInstruction.from_solders(ssp.create_account_with_seed(params.to_solders()))


def create_nonce_account(params: Union[CreateNonceAccountParams, CreateNonceAccountWithSeedParams]) -> Transaction:
    """Generate a Transaction that creates a new Nonce account.

    Args:
        params: The create nonce params.

    Returns:
        The transaction to create the new nonce account.
    """
    if isinstance(params, CreateNonceAccountParams):
        solders_ixs = ssp.create_nonce_account(
            from_pubkey=params.from_pubkey.to_solders(),
            nonce_pubkey=params.nonce_pubkey.to_solders(),
            authority=params.authorized_pubkey.to_solders(),
            lamports=params.lamports,
        )
    else:
        solders_ixs = ssp.create_nonce_account_with_seed(
            from_pubkey=params.from_pubkey.to_solders(),
            nonce_pubkey=params.nonce_pubkey.to_solders(),
            base=params.base_pubkey.to_solders(),
            seed=params.seed,
            authority=params.authorized_pubkey.to_solders(),
            lamports=params.lamports,
        )
    create_account_instruction = TransactionInstruction.from_solders(solders_ixs[0])
    initialize_nonce_instruction = TransactionInstruction.from_solders(solders_ixs[1])
    return Transaction(fee_payer=params.from_pubkey).add(create_account_instruction, initialize_nonce_instruction)


def nonce_initialization(params: InitializeNonceParams) -> TransactionInstruction:
    """Generate an instruction to initialize a Nonce account.

    Args:
        params: The nonce initialization params.

    Returns:
        The instruction to initialize the nonce account.

    """
    return TransactionInstruction.from_solders(ssp.initialize_nonce_account(params.to_solders()))


def nonce_advance(params: AdvanceNonceParams) -> TransactionInstruction:
    """Generate an instruction to advance the nonce in a Nonce account.

    Args:
        params: The advance nonce params

    Returns:
        The instruction to advance the nonce.
    """
    return TransactionInstruction.from_solders(ssp.advance_nonce_account(params.to_solders()))


def nonce_withdraw(params: WithdrawNonceParams) -> TransactionInstruction:
    """Generate an instruction that withdraws lamports from a Nonce account.

    Args:
        params: The withdraw nonce params

    Returns:
        The instruction to withdraw from the nonce account.
    """
    return TransactionInstruction.from_solders(ssp.withdraw_nonce_account(params.to_solders()))


def nonce_authorize(params: AuthorizeNonceParams) -> TransactionInstruction:
    """Generate an instruction that authorizes a new PublicKey as the authority on a Nonce account.

    Args:
        params: The authorize nonce params

    Returns:
        The instruction to grant the new nonce authority.
    """
    return TransactionInstruction.from_solders(ssp.authorize_nonce_account(params.to_solders()))


def allocate(params: Union[AllocateParams, AllocateWithSeedParams]) -> TransactionInstruction:
    """Generate an instruction that allocates space in an account without funding.

    Args:
        params: The allocate params.

    Example:

        >>> from solana.publickey import PublicKey
        >>> allocator = PublicKey(1)
        >>> instruction = allocate(
        ...     AllocateParams(account_pubkey=allocator, space=65537)
        ... )
        >>> type(instruction)
        <class 'solana.transaction.TransactionInstruction'>

    Returns:
        The allocate instruction.
    """
    if isinstance(params, AllocateWithSeedParams):
        solders_ix = ssp.allocate_with_seed(params.to_solders())
    else:
        solders_ix = ssp.allocate(params.to_solders())

    return TransactionInstruction.from_solders(solders_ix)
