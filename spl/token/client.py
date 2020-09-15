"""SPL Token program client."""
from __future__ import annotations

import time
from typing import Optional

import solana.system_program as sp
import spl.token.instructions as spl_token  # type: ignore # TODO: Don't ignore
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

    def __init__(self, endpoint: str, public_key: PublicKey, program_id: PublicKey, payer: Account) -> None:
        """Initialize a client to a SPL-Token program."""
        self._conn = conn
        self.pubkey, self.program_id, self.payer = public_key, program_id, payer

    def __send_and_confirm_transaction(
        self, txn: Transaction, *add_signers: Account, skip_preflight: bool = False
    ) -> str:
        # TODO: Make this a shared utility in the solana package.
        resp = self._conn.send_transaction(txn, self.payer, *add_signers, skip_preflight=skip_preflight)
        if resp.get("error"):
            raise Exception("Error sending transaction: ", resp["error"])
        # TODO: Confirm transaction.
        return resp["result"]

    @staticmethod
    def get_min_balance_rent_for_exempt_for_account(endpoint: str) -> int:
        """Get the minimum balance for the account to be rent exempt.

        :param endpoint: Endpoint to a solana cluster.
        """
        resp = Client(endpoint).get_minimum_balance_for_rent_exemption(ACCOUNT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def get_min_balance_rent_for_exempt_for_mint(endpoint: str) -> int:
        """Get the minimum balance for the mint to be rent exempt.

        :param endpoint: Endpoint to a solana cluster.
        """
        resp = Client(endpoint).get_minimum_balance_for_rent_exemption(MINT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def get_min_balance_rent_for_exempt_for_multisig(endpoint: str) -> int:
        """Get the minimum balance for the multsig to be rent exempt.

        :param endpoint: Endpoint to a solana cluster.
        """
        resp = Client(endpoint).get_minimum_balance_for_rent_exemption(MULTISIG_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def create_mint(  # pylint: disable=too-many-arguments  # TODO: Test this method
        endpoint: str,
        payer: Account,
        mint_authority: PublicKey,
        decimals: int,
        program_id: PublicKey,
        freeze_authority: Optional[PublicKey],
    ) -> Token:
        """Create and initialize a token.

        :param endpoint: Endpoint to a solana cluster.
        :param payer: Fee payer for transaction.
        :param mint_authority: Account or multisig that will control minting.
        :param decimals: Location of the decimal place.
        :param program_id: SPL Token program account.
        :param freeze_authority: (optional) Account or multisig that can freeze token accounts.
        """
        mint_account = Account()
        # Allocate memory for the account
        balance_needed = Token.get_min_balance_rent_for_exempt_for_account(endpoint)
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
        # Send transaction
        tx_sig = token.__send_and_confirm_transaction(txn, mint_account, skip_preflight=True)
        print(tx_sig)
        time.sleep(25)
        print(conn.get_confirmed_transaction(tx_sig))

        return token
