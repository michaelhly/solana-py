# pylint: disable=too-many-arguments
"""Helper code for client.py and async_client.py."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, NamedTuple, Optional, Tuple, Type, Union

import solana.system_program as sp
import spl.token.instructions as spl_token
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment, Confirmed
from solana.rpc.types import TokenAccountOpts, TxOpts
from solana.transaction import Transaction
from spl.token._layouts import ACCOUNT_LAYOUT, MINT_LAYOUT
from spl.token.constants import WRAPPED_SOL_MINT

if TYPE_CHECKING:
    from spl.token.async_client import AsyncToken  # noqa: F401
    from spl.token.client import Token  # noqa: F401


class AccountInfo(NamedTuple):
    """Information about an account."""

    mint: PublicKey
    """The mint associated with this account."""
    owner: PublicKey
    """Owner of this account."""
    amount: int
    """Amount of tokens this account holds."""
    delegate: Optional[PublicKey]
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
    close_authority: Optional[PublicKey]
    """Optional authority to close the account."""


class MintInfo(NamedTuple):
    """Information about the mint."""

    mint_authority: Optional[PublicKey]
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
    freeze_authority: Optional[PublicKey]
    """ Optional authority to freeze token accounts."""


class _TokenCore:  # pylint: disable=too-few-public-methods

    pubkey: PublicKey
    """The public key identifying this mint."""

    program_id: PublicKey
    """Program Identifier for the Token program."""

    payer: Account
    """Fee payer."""

    def __init__(self, pubkey: PublicKey, program_id: PublicKey, payer: Account) -> None:
        """Initialize a client to a SPL-Token program."""
        self.pubkey, self.program_id, self.payer = pubkey, program_id, payer

    def _get_accounts_args(
        self,
        owner: PublicKey,
        commitment: Commitment = Confirmed,
        encoding: str = "jsonParsed",
    ) -> Tuple[PublicKey, TokenAccountOpts, Commitment]:
        return owner, TokenAccountOpts(mint=self.pubkey, encoding=encoding), commitment

    @staticmethod
    def _create_mint_args(
        conn: Union[Client, AsyncClient],
        payer: Account,
        mint_authority: PublicKey,
        decimals: int,
        program_id: PublicKey,
        freeze_authority: Optional[PublicKey],
        skip_confirmation: bool,
        balance_needed: int,
        cls: Union[Type[Token], Type[AsyncToken]],
    ) -> Tuple[Union[Token, AsyncToken], Transaction, Account, Account, TxOpts]:
        mint_account = Account()
        token = cls(conn, mint_account.public_key(), program_id, payer)  # type: ignore
        # Construct transaction
        txn = Transaction()
        txn.add(
            sp.create_account(
                sp.CreateAccountParams(
                    from_pubkey=payer.public_key(),
                    new_account_pubkey=mint_account.public_key(),
                    lamports=balance_needed,
                    space=MINT_LAYOUT.sizeof(),
                    program_id=program_id,
                )
            )
        )
        txn.add(
            spl_token.initialize_mint(
                spl_token.InitializeMintParams(
                    program_id=program_id,
                    mint=mint_account.public_key(),
                    decimals=decimals,
                    mint_authority=mint_authority,
                    freeze_authority=freeze_authority,
                )
            )
        )
        return token, txn, payer, mint_account, TxOpts(skip_confirmation=skip_confirmation, skip_preflight=True)

    def _create_account_args(
        self,
        owner: PublicKey,
        skip_confirmation: bool,
        balance_needed: int,
    ) -> Tuple[PublicKey, Transaction, Account, Account, TxOpts]:
        new_account = Account()
        # Allocate memory for the account

        # Construct transaction
        txn = Transaction()
        txn.add(
            sp.create_account(
                sp.CreateAccountParams(
                    from_pubkey=self.payer.public_key(),
                    new_account_pubkey=new_account.public_key(),
                    lamports=balance_needed,
                    space=ACCOUNT_LAYOUT.sizeof(),
                    program_id=self.program_id,
                )
            )
        )
        txn.add(
            spl_token.initialize_account(
                spl_token.InitializeAccountParams(
                    account=new_account.public_key(), mint=self.pubkey, owner=owner, program_id=self.program_id
                )
            )
        )
        return (
            new_account.public_key(),
            txn,
            self.payer,
            new_account,
            TxOpts(skip_preflight=True, skip_confirmation=skip_confirmation),
        )

    def _create_associated_token_account_args(
        self,
        owner: PublicKey,
        skip_confirmation: bool,
    ) -> Tuple[PublicKey, Transaction, Account, TxOpts]:

        # Construct transaction
        txn = Transaction()
        create_txn = spl_token.create_associated_token_account(
            payer=self.payer.public_key(), owner=owner, mint=self.pubkey
        )
        txn.add(create_txn)
        return create_txn.keys[1].pubkey, txn, self.payer, TxOpts(skip_confirmation=skip_confirmation)

    @staticmethod
    def _create_wrapped_native_account_args(
        program_id: PublicKey,
        owner: PublicKey,
        payer: Account,
        amount: int,
        skip_confirmation: bool,
        balance_needed: int,
    ) -> Tuple[PublicKey, Transaction, Account, Account, TxOpts]:
        new_account = Account()
        # Allocate memory for the account
        # Construct transaction
        txn = Transaction()
        txn.add(
            sp.create_account(
                sp.CreateAccountParams(
                    from_pubkey=payer.public_key(),
                    new_account_pubkey=new_account.public_key(),
                    lamports=balance_needed,
                    space=ACCOUNT_LAYOUT.sizeof(),
                    program_id=program_id,
                )
            )
        )

        txn.add(
            sp.transfer(
                sp.TransferParams(from_pubkey=payer.public_key(), to_pubkey=new_account.public_key(), lamports=amount)
            )
        )

        txn.add(
            spl_token.initialize_account(
                spl_token.InitializeAccountParams(
                    account=new_account.public_key(), mint=WRAPPED_SOL_MINT, owner=owner, program_id=program_id
                )
            )
        )

        return new_account.public_key(), txn, payer, new_account, TxOpts(skip_confirmation=skip_confirmation)

    def _transfer_args(
        self,
        source: PublicKey,
        dest: PublicKey,
        owner: Union[Account, PublicKey],
        amount: int,
        multi_signers: Optional[List[Account]],
        opts: TxOpts,
    ) -> Tuple[Transaction, List[Account], TxOpts]:
        if isinstance(owner, Account):
            owner_pubkey = owner.public_key()
            signers = [owner]
        else:
            owner_pubkey = owner
            signers = multi_signers if multi_signers else []

        txn = Transaction().add(
            spl_token.transfer(
                spl_token.TransferParams(
                    program_id=self.program_id,
                    source=source,
                    dest=dest,
                    owner=owner_pubkey,
                    amount=amount,
                    signers=[signer.public_key() for signer in signers],
                )
            )
        )
        return txn, signers, opts

    def _set_authority_args(
        self,
        account: PublicKey,
        current_authority: Union[Account, PublicKey],
        authority_type: spl_token.AuthorityType,
        new_authority: Optional[PublicKey],
        multi_signers: Optional[List[Account]],
        opts: TxOpts = TxOpts(),
    ) -> Tuple[Transaction, Account, List[Account], TxOpts]:
        if isinstance(current_authority, Account):
            current_authority_pubkey = current_authority.public_key()
            signers = [current_authority]
        else:
            current_authority_pubkey = current_authority
            signers = multi_signers if multi_signers else []

        txn = Transaction().add(
            spl_token.set_authority(
                spl_token.SetAuthorityParams(
                    program_id=self.program_id,
                    account=account,
                    authority=authority_type,
                    current_authority=current_authority_pubkey,
                    signers=[signer.public_key() for signer in signers],
                    new_authority=new_authority,
                )
            )
        )

        return txn, self.payer, signers, opts

    def _mint_to_args(
        self,
        dest: PublicKey,
        mint_authority: Union[Account, PublicKey],
        amount: int,
        multi_signers: Optional[List[Account]],
        opts: TxOpts,
    ) -> Tuple[Transaction, List[Account], TxOpts]:
        if isinstance(mint_authority, Account):
            owner_pubkey = mint_authority.public_key()
            signers = [mint_authority]
        else:
            owner_pubkey = mint_authority
            signers = multi_signers if multi_signers else []

        txn = Transaction().add(
            spl_token.mint_to(
                spl_token.MintToParams(
                    program_id=self.program_id,
                    mint=self.pubkey,
                    dest=dest,
                    mint_authority=owner_pubkey,
                    amount=amount,
                    signers=[signer.public_key() for signer in signers],
                )
            )
        )
        return txn, signers, opts
