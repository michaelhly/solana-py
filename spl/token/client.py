"""SPL Token program client."""
from __future__ import annotations

from typing import Optional

import solana.system_program as sp
import spl.token.instructions as spl_token
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.transaction import Transaction
from spl.token._layouts import ACCOUNT_LAYOUT, MINT_LAYOUT, MULTISIG_LAYOUT  # type: ignore


class Token:
    """An ERC20-like Token."""

    pubkey: PublicKey
    """The public key identifying this mint."""

    program_id: PublicKey
    """Program Identifier for the Token program."""

    payer: Account
    """Fee payer."""

    def __init__(self, conn: Client, pubkey: PublicKey, program_id: PublicKey, payer: Account) -> None:
        """Initialize a client to a SPL-Token program."""
        self._conn = conn
        self.pubkey, self.program_id, self.payer = pubkey, program_id, payer

    @staticmethod
    def get_min_balance_rent_for_exempt_for_account(conn: Client) -> int:
        """Get the minimum balance for the account to be rent exempt.

        :param conn: RPC connection to a solana cluster.
        """
        resp = conn.get_minimum_balance_for_rent_exemption(ACCOUNT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def get_min_balance_rent_for_exempt_for_mint(conn: Client) -> int:
        """Get the minimum balance for the mint to be rent exempt.

        :param conn: RPC connection to a solana cluster.
        """
        resp = conn.get_minimum_balance_for_rent_exemption(MINT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def get_min_balance_rent_for_exempt_for_multisig(conn: Client) -> int:
        """Get the minimum balance for the multsig to be rent exempt.

        :param conn: RPC connection to a solana cluster.
        """
        resp = conn.get_minimum_balance_for_rent_exemption(MULTISIG_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def create_mint(  # pylint: disable=too-many-arguments  # TODO: Test this method
        conn: Client,
        payer: Account,
        mint_authority: PublicKey,
        decimals: int,
        program_id: PublicKey,
        freeze_authority: Optional[PublicKey] = None,
    ) -> Token:
        """Create and initialize a token.

        :param conn: RPC connection to a solana cluster.
        :param payer: Fee payer for transaction.
        :param mint_authority: Account or multisig that will control minting.
        :param decimals: Location of the decimal place.
        :param program_id: SPL Token program account.
        :param freeze_authority: (optional) Account or multisig that can freeze token accounts.
        """
        mint_account = Account()
        token = Token(conn, mint_account.public_key(), program_id, payer)
        # Allocate memory for the account
        balance_needed = Token.get_min_balance_rent_for_exempt_for_mint(conn)
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
        # Send the two instructions
        conn.send_and_confirm_transaction(txn, payer, mint_account, skip_preflight=True)
        return token

    def create_account(self, owner: PublicKey) -> PublicKey:
        """Create and initialize a new account.

        This account may then be used as a `transfer()` or `approve()` destination.

        :param owner: User account that will own the new account.
        """
        new_account = Account()
        # Allocate memory for the account
        balance_needed = Token.get_min_balance_rent_for_exempt_for_account(self._conn)
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
        # Send the two instructions
        self._conn.send_and_confirm_transaction(txn, self.payer, new_account, skip_preflight=True)
        return new_account.public_key()
