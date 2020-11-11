# pylint: disable=too-many-arguments
"""SPL Token program client."""
from __future__ import annotations

from typing import List, NamedTuple, Optional, Union

import solana.system_program as sp
import spl.token.instructions as spl_token
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment, Single
from solana.rpc.types import RPCResponse, TokenAccountOpts, TxOpts
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


class Token:  # pylint: disable=too-many-public-methods
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

    def get_accounts(self, owner: PublicKey, is_delegate: bool = False, encoding: str = "jsonParsed") -> RPCResponse:
        """Get token accounts of the provided owner by the token's mint.

        :param owner: Public Key of the token account owner.
        :param is_delegate: (optional) Flag specifying if the `owner` public key is a delegate.
        :param encoding: (optional) Encoding for Account data, either "base58" (slow), "base64" or jsonParsed".

        Parsed-JSON encoding attempts to use program-specific state parsers to return more
        human-readable and explicit account state data. If parsed-JSON is requested but a
        valid mint cannot be found for a particular account, that account will be filtered out
        from results. jsonParsed encoding is UNSTABLE.
        """
        return (
            self._conn.get_token_accounts_by_delegate(owner, TokenAccountOpts(mint=self.pubkey, encoding=encoding))
            if is_delegate
            else self._conn.get_token_accounts_by_owner(owner, TokenAccountOpts(mint=self.pubkey, encoding=encoding))
        )

    def get_balance(self, pubkey: PublicKey, commitment: Commitment = Single) -> RPCResponse:
        """Get the balance of the provided token account.

        :param pubkey: Public Key of the token account.
        :param commitment: (optional) Bank state to query.
        """
        return self._conn.get_token_account_balance(pubkey, commitment)

    @staticmethod
    def create_mint(
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
        conn.send_transaction(
            txn, payer, mint_account, opts=TxOpts(skip_confirmation=skip_confirmation, skip_preflight=True)
        )
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
        self._conn.send_transaction(
            txn, self.payer, new_account, opts=TxOpts(skip_preflight=True, skip_confirmation=skip_confirmation)
        )
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

    def transfer(
        self,
        source: PublicKey,
        dest: PublicKey,
        owner: Union[Account, PublicKey],
        amount: int,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Transfer tokens to another account.

        :param source: Public key of account to transfer tokens from.
        :param dest: Public key of account to transfer tokens to.
        :param owner: Owner of the source account.
        :param amount: Number of tokens to transfer.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
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
        return self._conn.send_transaction(txn, *signers, opts=opts)

    def approve(
        self,
        account: PublicKey,
        delegate: PublicKey,
        owner: PublicKey,
        amount: int,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Grant a third-party permission to transfer up the specified number of tokens from an account.

        :param source: Public key of the source account.
        :param delegate: Account authorized to perform a transfer tokens from the source account.
        :param owner: Owner of the source account.
        :param amount: Maximum number of tokens the delegate may transfer.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("approve not implemented")

    def revoke(
        self,
        account: PublicKey,
        owner: PublicKey,
        multi_signers: Optional[List[Account]],
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Remove approval for the transfer of any remaining tokens.

        :param account:  Delegate account authorized to perform a transfer of tokens from the source account.
        :param owner: Owner of the source account.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("revoke not implemented")

    def set_authority(
        self,
        account: PublicKey,
        current_authority: PublicKey,
        authority_type: spl_token.AuthorityType,
        new_authority: Optional[PublicKey] = None,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Assign a new authority to the account.

        :param account: Public key of the token account.
        :param current_authority: Current authority of the account.
        :param authority_type: Type of authority to set.
        :param new_authority: (optional) New authority of the account.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("set_authority not implemented")

    def mint_to(
        self,
        dest: PublicKey,
        mint_authority: Union[Account, PublicKey],
        amount: int,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Mint new tokens.

        :param dest: Public key of the account to mint to.
        :param mint_authority: Public key of the minting authority.
        :param amount: Amount to mint.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
        """
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
        return self._conn.send_transaction(txn, *signers, opts=opts)

    def burn(
        self,
        account: PublicKey,
        owner: PublicKey,
        amount: int,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Burn tokens.

        :param account: Account to burn tokens from.
        :param owner: Owner of the account.
        :param amount: Amount to burn.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("burn not implemented")

    def close_account(
        self,
        account: PublicKey,
        dest: PublicKey,
        authority: PublicKey,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Remove approval for the transfer of any remaining tokens.

        :param account: Account to close.
        :param dest: Account to receive the remaining balance of the closed account.
        :param authority: Authority which is allowed to close the account.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("close_account not implemented")

    def freeze_account(
        self, account: PublicKey, authority: PublicKey, multi_signers: Optional[List[Account]]
    ) -> RPCResponse:
        """Freeze account.

        :param account: Account to freeze.
        :param authority: The mint freeze authority.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        """
        raise NotImplementedError("freeze_account not implemented")

    def thaw_account(
        self,
        account: PublicKey,
        authority: PublicKey,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Thaw account.

        :param account: Account to thaw.
        :param authority: The mint freeze authority.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("thaw_account not implemented")

    def transfer2(
        self,
        source: PublicKey,
        dest: PublicKey,
        owner: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Account]],
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Transfer tokens to another account, asserting the token mint and decimals.

        :param source: Public key of account to transfer tokens from.
        :param dest: Public key of account to transfer tokens to.
        :param owner: Owner of the source account.
        :param amount: Number of tokens to transfer.
        :param decimals: Number of decimals in transfer amount.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("transfer2 not implemented")

    def approve2(
        self,
        account: PublicKey,
        delegate: PublicKey,
        owner: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Grant a third-party permission to transfer up the specified number of tokens from an account.

        This method also asserts the token mint and decimals.

        :param source: Public key of the source account.
        :param delegate: Account authorized to perform a transfer tokens from the source account.
        :param owner: Owner of the source account.
        :param amount: Maximum number of tokens the delegate may transfer.
        :param decimals: Number of decimals in approve amount.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("approve2 not implemented")

    def mint_to2(
        self,
        dest: PublicKey,
        mint_authority: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Mint new tokens, asserting the token mint and decimals.

        :param dest: Public key of the account to mint to.
        :param mint_authority: Public key of the minting authority.
        :param amount: Amount to mint.
        :param decimals: Number of decimals in amount to mint.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("mint_to2 not implemented")

    def burn2(
        self,
        account: PublicKey,
        owner: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Account]] = None,
        opts: TxOpts = TxOpts(),
    ) -> RPCResponse:
        """Burn tokens, asserting the token mint and decimals.

        :param account: Account to burn tokens from.
        :param owner: Owner of the account.
        :param amount: Amount to burn.
        :param decimals: Number of decimals in amount to burn.
        :param multi_signers: (optional) Signing accounts if `owner` is a multiSig.
        :param opts: (optional) Transaction options.
        """
        raise NotImplementedError("burn2 not implemented")
