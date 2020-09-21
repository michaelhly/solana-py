"""SPL Token program client."""
from __future__ import annotations

from typing import List, NamedTuple, Optional

import solana.system_program as sp
import spl.token.instructions as spl_token
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import RPCResponse
from solana.transaction import Transaction
from spl.token._layouts import ACCOUNT_LAYOUT, MINT_LAYOUT, MULTISIG_LAYOUT  # type: ignore


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

    def __send_transaction(
        self, txn: Transaction, *signers: Account, skip_preflight: bool, skip_conf: bool
    ) -> RPCResponse:
        if skip_conf:
            return self._conn.send_transaction(txn, *signers, skip_preflight=skip_preflight)
        try:
            resp = self._conn.send_and_confirm_transaction(txn, *signers, skip_preflight=skip_preflight)
            err = resp["result"].get("meta").get("err") or resp.get("error")
            if err:
                raise Exception("Transaction error: ", err)
        except Exception as excep:
            raise Exception("Failed to confirm transaction") from excep
        return resp

    @staticmethod
    def get_min_balance_rent_for_exempt_for_account(conn: Client) -> int:
        """Get the minimum balance for the account to be rent exempt.

        :param conn: RPC connection to a solana cluster.
        :return: Number of lamports required.
        """
        resp = conn.get_minimum_balance_for_rent_exemption(ACCOUNT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def get_min_balance_rent_for_exempt_for_mint(conn: Client) -> int:
        """Get the minimum balance for the mint to be rent exempt.

        :param conn: RPC connection to a solana cluster.
        :return: Number of lamports required.
        """
        resp = conn.get_minimum_balance_for_rent_exemption(MINT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def get_min_balance_rent_for_exempt_for_multisig(conn: Client) -> int:
        """Get the minimum balance for the multsig to be rent exempt.

        :param conn: RPC connection to a solana cluster.
        :return: Number of lamports required.
        """
        resp = conn.get_minimum_balance_for_rent_exemption(MULTISIG_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    def create_mint(  # pylint: disable=too-many-arguments
        conn: Client,
        payer: Account,
        mint_authority: PublicKey,
        decimals: int,
        program_id: PublicKey,
        freeze_authority: Optional[PublicKey] = None,
        skip_confirmation: bool = False,
    ) -> Token:
        """Create and initialize a token.

        :param conn: RPC connection to a solana cluster.
        :param payer: Fee payer for transaction.
        :param mint_authority: Account or multisig that will control minting.
        :param decimals: Location of the decimal place.
        :param program_id: SPL Token program account.
        :param freeze_authority: (optional) Account or multisig that can freeze token accounts.
        :param skip_confirmation: (optional) Option to skip transaction confirmation.
        :return: Token object for the newly minted token.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
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
        if skip_confirmation:
            conn.send_transaction(txn, payer, mint_account, skip_preflight=True)
        else:
            try:
                resp = conn.send_and_confirm_transaction(txn, payer, mint_account, skip_preflight=True)
                err = resp["result"].get("meta").get("err") or resp.get("error")
                if err:
                    raise Exception("Transaction error: ", err)
            except Exception as excep:
                raise Exception("Failed to confirm transaction") from excep

        return token

    def create_account(
        self,
        owner: PublicKey,
        skip_confirmation: bool = False,
    ) -> PublicKey:
        """Create and initialize a new account.

        This account may then be used as a `transfer()` or `approve()` destination.

        :param owner: User account that will own the new account.
        :param skip_confirmation: (optional) Option to skip transaction confirmation.
        :return: Public key of the new empty account.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
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
        self.__send_transaction(txn, self.payer, new_account, skip_preflight=True, skip_conf=skip_confirmation)
        return new_account.public_key()

    @staticmethod
    def create_wrapped_native_account(
        conn: Client, program_id: PublicKey, owner: PublicKey, payer: Account, amount: int
    ) -> PublicKey:
        """Create and initialize a new account on the special native token mint.

        :param conn: RPC connection to a solana cluster.
        :param program_id: SPL Token program account.
        :param owner: The owner of the new token account.
        :param payer: The source of the lamports to initialize, and payer of the initialization fees.
        :param amount: The amount of lamports to wrap.
        :return: The new token account.
        """
        raise NotImplementedError("create_wrapped_native_account not implemented")

    def create_multisig(self, m: int, signers: List[PublicKey]) -> PublicKey:  # pylint: disable=invalid-name
        """Create and initialize a new multisig.

        :param m: Number of required signatures.
        :param signers: Full set of signers.
        :return: Public key of the new multisig account.
        """
        raise NotImplementedError("create_multisig not implemented")

    def get_mint_info(self) -> MintInfo:
        """Retrieve mint information."""
        raise NotImplementedError("get_mint_info not implemented")

    def get_account_info(self) -> AccountInfo:
        """Retrieve account information."""
        raise NotImplementedError("get_account_info not implemented")

    def transfer(  # pylint: disable=too-many-arguments
        self, source: PublicKey, dest: PublicKey, owner: PublicKey, amount: int, signers: Optional[List[Account]]
    ) -> RPCResponse:
        """Transfer tokens to another account.

        :param source: Public key of account to transfer tokens from.
        :param dest: Public key of account to transfer tokens to.
        :param owner: Owner of the source account.
        :param amount: Number of tokens to transfer.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("transfer not implemented")

    def approve(  # pylint: disable=too-many-arguments
        self, account: PublicKey, delegate: PublicKey, owner: PublicKey, amount: int, signers: Optional[List[Account]]
    ) -> RPCResponse:
        """Transfer tokens to another account.

        :param source: Public key of the source account.
        :param delegate: Account authorized to perform a transfer tokens from the source account.
        :param owner: Owner of the source account.
        :param amount: Maximum number of tokens the delegate may transfer.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("approve not implemented")

    def revoke(self, account: PublicKey, owner: PublicKey, signers: Optional[List[Account]]) -> RPCResponse:
        """Remove approval for the transfer of any remaining tokens.

        :param account:  Delegate account authorized to perform a transfer of tokens from the source account.
        :param owner: Owner of the source account.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("revoke not implemented")

    def set_authority(  # pylint: disable=too-many-arguments
        self,
        account: PublicKey,
        current_authority: PublicKey,
        authority_type: spl_token.AuthorityType,
        new_authority: Optional[PublicKey],
        signers: Optional[List[Account]],
    ) -> RPCResponse:
        """Assign a new authority to the account.

        :param account: Public key of the token account.
        :param current_authority: Current authority of the account.
        :param authority_type: Type of authority to set.
        :param new_authority: (optional) New authority of the account.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("set_authority not implemented")

    def mint_to(
        self, dest: PublicKey, mint_authority: PublicKey, amount: int, signers: Optional[List[Account]]
    ) -> RPCResponse:
        """Mint new tokens.

        :param dest: Public key of the account to mint to.
        :param mint_authority: Public key of the minting authority.
        :param amount: Amount to mint.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("mint_to not implemented")

    def burn(self, account: PublicKey, owner: PublicKey, amount: int, signers: Optional[List[Account]]) -> RPCResponse:
        """Burn tokens.

        :param account: Account to burn tokens from.
        :param owner: Owner of the account.
        :param amount: Amount to burn.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("burn not implemented")

    def close_account(
        self, account: PublicKey, dest: PublicKey, authority: PublicKey, signers: Optional[List[Account]]
    ) -> RPCResponse:
        """Remove approval for the transfer of any remaining tokens.

        :param account: Account to close.
        :param dest: Account to receive the remaining balance of the closed account.
        :param authority: Authority which is allowed to close the account.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("close_account not implemented")

    def freeze_account(self, account: PublicKey, authority: PublicKey, signers: Optional[List[Account]]) -> RPCResponse:
        """Freeze account.

        :param account: Account to freeze.
        :param authority: The mint freeze authority.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("freeze_account not implemented")

    def thaw_account(self, account: PublicKey, authority: PublicKey, signers: Optional[List[Account]]) -> RPCResponse:
        """Thaw account.

        :param account: Account to thaw.
        :param authority: The mint freeze authority.
        :param signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("thaw_account not implemented")
