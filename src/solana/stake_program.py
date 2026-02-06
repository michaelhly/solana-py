"""Library to interface with the stake program."""
from typing import NamedTuple, Union

from solders import sysvar
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.system_program import (
    CreateAccountParams,
    CreateAccountWithSeedParams,
    create_account,
    create_account_with_seed,
)

from solana._layouts.stake_instructions import STAKE_INSTRUCTIONS_LAYOUT, StakeInstructionType
from solana.transaction import Transaction

STAKE_CONFIG_PUBKEY: Pubkey = Pubkey.from_string("StakeConfig11111111111111111111111111111111")
STAKE_PUBKEY: Pubkey = Pubkey.from_string("Stake11111111111111111111111111111111111111")


class Authorized(NamedTuple):
    """Staking account authority info."""

    staker: Pubkey
    """"""
    withdrawer: Pubkey
    """"""


class Lockup(NamedTuple):
    """Stake account lockup info."""

    unix_timestamp: int
    """"""
    epoch: int
    """"""
    custodian: Pubkey


class InitializeStakeParams(NamedTuple):
    """Initialize Staking params."""

    stake_pubkey: Pubkey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""


class CreateStakeAccountParams(NamedTuple):
    """Create stake account transaction params."""

    from_pubkey: Pubkey
    """"""
    stake_pubkey: Pubkey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""
    lamports: int
    """"""


class CreateStakeAccountWithSeedParams(NamedTuple):
    """Create stake account with seed transaction params."""

    from_pubkey: Pubkey
    """"""
    stake_pubkey: Pubkey
    """"""
    base_pubkey: Pubkey
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

    stake_pubkey: Pubkey
    """"""
    authorized_pubkey: Pubkey
    """"""
    vote_pubkey: Pubkey
    """"""


class CreateAccountAndDelegateStakeParams(NamedTuple):
    """Create and delegate a stake account transaction params."""

    from_pubkey: Pubkey
    """"""
    stake_pubkey: Pubkey
    """"""
    vote_pubkey: Pubkey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""
    lamports: int
    """"""


class CreateAccountWithSeedAndDelegateStakeParams(NamedTuple):
    """Create and delegate stake account with seed transaction params."""

    from_pubkey: Pubkey
    """"""
    stake_pubkey: Pubkey
    """"""
    base_pubkey: Pubkey
    """"""
    seed: str
    """"""
    vote_pubkey: Pubkey
    """"""
    authorized: Authorized
    """"""
    lockup: Lockup
    """"""
    lamports: int
    """"""


class WithdrawStakeParams(NamedTuple):
    """Withdraw stake account params."""

    stake_pubkey: Pubkey
    """"""
    withdrawer_pubkey: Pubkey
    """"""
    to_pubkey: Pubkey
    """"""
    lamports: int
    """"""
    custodian_pubkey: Pubkey
    """"""


def withdraw_stake(params: WithdrawStakeParams) -> Transaction:
    """Withdraw stake."""
    data = STAKE_INSTRUCTIONS_LAYOUT.build(
        {"instruction_type:": StakeInstructionType.WITHDRAW_STAKE_ACCOUNT, "args": {"lamports": params.lamports}}
    )

    withdraw_instruction = Instruction(
        accounts=[
            AccountMeta(pubkey=params.stake_pubkey, is_signer=True, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.to_pubkey, is_signer=False, is_writable=True),
        ],
        program_id=Pubkey.default(),
        data=data,
    )

    return Transaction(fee_payer=params.stake_pubkey).add(withdraw_instruction)


def create_account_and_delegate_stake(
    params: Union[CreateAccountAndDelegateStakeParams, CreateAccountWithSeedAndDelegateStakeParams]
) -> Transaction:
    """Generate a transaction to crate and delegate a stake account."""
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
            authorized_pubkey=params.authorized.staker,
            vote_pubkey=params.vote_pubkey,
        )
    )

    return Transaction(fee_payer=params.from_pubkey).add(
        create_account_instruction, initialize_stake_instruction, delegate_stake_instruction
    )


def delegate_stake(params: DelegateStakeParams) -> Instruction:
    """Generate an instruction to delete a Stake account."""
    data = STAKE_INSTRUCTIONS_LAYOUT.build(
        {"instruction_type": StakeInstructionType.DELEGATE_STAKE_ACCOUNT, "args": {}}
    )
    return Instruction(
        accounts=[
            AccountMeta(pubkey=params.stake_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=params.vote_pubkey, is_signer=False, is_writable=False),
            AccountMeta(pubkey=sysvar.CLOCK, is_signer=False, is_writable=False),
            AccountMeta(pubkey=sysvar.STAKE_HISTORY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=STAKE_CONFIG_PUBKEY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=params.authorized_pubkey, is_signer=True, is_writable=False),
        ],
        program_id=STAKE_PUBKEY,
        data=data,
    )


def initialize_stake(params: InitializeStakeParams) -> Instruction:
    """Initialize stake."""
    data = STAKE_INSTRUCTIONS_LAYOUT.build(
        {
            "instruction_type": StakeInstructionType.INITIALIZE_STAKE_ACCOUNT,
            "args": {
                "authorized": {
                    "staker": params.authorized.staker.__bytes__(),
                    "withdrawer": params.authorized.withdrawer.__bytes__(),
                },
                "lockup": {
                    "unix_timestamp": params.lockup.unix_timestamp,
                    "epoch": params.lockup.epoch,
                    "custodian": params.lockup.custodian.__bytes__(),
                },
            },
        }
    )

    return Instruction(
        accounts=[
            AccountMeta(pubkey=params.stake_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=sysvar.RENT, is_signer=False, is_writable=False),
        ],
        program_id=STAKE_PUBKEY,
        data=data,
    )


def _create_stake_account_instruction(
    params: Union[
        CreateStakeAccountParams,
        CreateStakeAccountWithSeedParams,
        CreateAccountAndDelegateStakeParams,
        CreateAccountWithSeedAndDelegateStakeParams,
    ]
) -> Instruction:
    if isinstance(params, (CreateAccountAndDelegateStakeParams, CreateStakeAccountParams)):
        return create_account(
            CreateAccountParams(
                from_pubkey=params.from_pubkey,
                to_pubkey=params.stake_pubkey,
                lamports=params.lamports,
                space=200,
                owner=STAKE_PUBKEY,
            )
        )
    return create_account_with_seed(
        CreateAccountWithSeedParams(
            from_pubkey=params.from_pubkey,
            to_pubkey=params.stake_pubkey,
            base=params.base_pubkey,
            seed=params.seed,
            lamports=params.lamports,
            space=200,
            owner=STAKE_PUBKEY,
        )
    )


def create_stake_account(params: Union[CreateStakeAccountParams, CreateStakeAccountWithSeedParams]) -> Transaction:
    """Generate a Transaction that creates a new Staking Account."""
    initialize_stake_instruction = initialize_stake(
        InitializeStakeParams(
            stake_pubkey=params.stake_pubkey,
            authorized=params.authorized,
            lockup=params.lockup,
        )
    )

    create_account_instruction = _create_stake_account_instruction(params=params)

    return Transaction(fee_payer=params.from_pubkey).add(create_account_instruction, initialize_stake_instruction)
