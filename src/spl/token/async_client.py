# pylint: disable=too-many-arguments
"""Async SPL Token program client."""
from __future__ import annotations

from typing import List, Optional, Union, cast

import spl.token.instructions as spl_token
from solana.blockhash import Blockhash
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.rpc.types import RPCResponse, TxOpts
from spl.token._layouts import ACCOUNT_LAYOUT, MINT_LAYOUT, MULTISIG_LAYOUT
from spl.token.core import AccountInfo, MintInfo, _TokenCore


class AsyncToken(_TokenCore):  # pylint: disable=too-many-public-methods
    """An ERC20-like Token."""

    def __init__(self, conn: AsyncClient, pubkey: PublicKey, program_id: PublicKey, payer: Keypair) -> None:
        """Initialize a client to a SPL-Token program."""
        super().__init__(pubkey, program_id, payer)
        self._conn = conn

    @staticmethod
    async def get_min_balance_rent_for_exempt_for_account(conn: AsyncClient) -> int:
        """Get the minimum balance for the account to be rent exempt.

        Args:
            conn: RPC connection to a solana cluster.

        Returns:
            Number of lamports required.
        """
        resp = await conn.get_minimum_balance_for_rent_exemption(ACCOUNT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    async def get_min_balance_rent_for_exempt_for_mint(conn: AsyncClient) -> int:
        """Get the minimum balance for the mint to be rent exempt.

        Args:
            conn: RPC connection to a solana cluster.

        Returns:
            Number of lamports required.
        """
        resp = await conn.get_minimum_balance_for_rent_exemption(MINT_LAYOUT.sizeof())
        return resp["result"]

    @staticmethod
    async def get_min_balance_rent_for_exempt_for_multisig(conn: AsyncClient) -> int:
        """Get the minimum balance for the multisig to be rent exempt.

        Args:
            conn: RPC connection to a solana cluster.

        Returns:
             Number of lamports required.
        """
        resp = await conn.get_minimum_balance_for_rent_exemption(MULTISIG_LAYOUT.sizeof())
        return resp["result"]

    async def get_accounts(
        self,
        owner: PublicKey,
        is_delegate: bool = False,
        commitment: Optional[Commitment] = None,
        encoding: str = "jsonParsed",
    ) -> RPCResponse:
        """Get token accounts of the provided owner by the token's mint.

        Args:
            owner: Public Key of the token account owner.
            is_delegate: (optional) Flag specifying if the `owner` public key is a delegate.
            encoding: (optional) Encoding for Account data, either "base58" (slow), "base64" or jsonParsed".
            commitment: (optional) Bank state to query.

        Parsed-JSON encoding attempts to use program-specific state parsers to return more
        human-readable and explicit account state data. If parsed-JSON is requested but a
        valid mint cannot be found for a particular account, that account will be filtered out
        from results. jsonParsed encoding is UNSTABLE.
        """
        args = self._get_accounts_args(
            owner, commitment, encoding, self._conn.commitment  # pylint: disable=protected-access
        )
        return (
            await self._conn.get_token_accounts_by_delegate(*args)
            if is_delegate
            else await self._conn.get_token_accounts_by_owner(*args)
        )

    async def get_balance(self, pubkey: PublicKey, commitment: Optional[Commitment] = None) -> RPCResponse:
        """Get the balance of the provided token account.

        Args:
            pubkey: Public Key of the token account.
            commitment: (optional) Bank state to query.
        """
        return await self._conn.get_token_account_balance(pubkey, commitment)

    @classmethod
    async def create_mint(
        cls,
        conn: AsyncClient,
        payer: Keypair,
        mint_authority: PublicKey,
        decimals: int,
        program_id: PublicKey,
        freeze_authority: Optional[PublicKey] = None,
        skip_confirmation: bool = False,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> AsyncToken:
        """Create and initialize a token.

        Args:
            conn: RPC connection to a solana cluster.
            payer: Fee payer for transaction.
            mint_authority: Account or multisig that will control minting.
            decimals: Location of the decimal place.
            program_id: SPL Token program account.
            freeze_authority: (optional) Account or multisig that can freeze token accounts.
            skip_confirmation: (optional) Option to skip transaction confirmation.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.

        Returns:
            Token object for the newly minted token.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
        """
        # Allocate memory for the account
        balance_needed = await AsyncToken.get_min_balance_rent_for_exempt_for_mint(conn)
        # Construct transaction
        token, txn, payer, mint_account, opts = _TokenCore._create_mint_args(
            conn,
            payer,
            mint_authority,
            decimals,
            program_id,
            freeze_authority,
            skip_confirmation,
            balance_needed,
            cls,
            conn.commitment,
        )
        # Send the two instructions
        await conn.send_transaction(txn, payer, mint_account, opts=opts, recent_blockhash=recent_blockhash)
        return cast(AsyncToken, token)

    async def create_account(
        self,
        owner: PublicKey,
        skip_confirmation: bool = False,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> PublicKey:
        """Create and initialize a new account.

        This account may then be used as a `transfer()` or `approve()` destination.

        Args:
            owner: User account that will own the new account.
            skip_confirmation: (optional) Option to skip transaction confirmation.

        Returns:
            Public key of the new empty account.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
        """
        balance_needed = await AsyncToken.get_min_balance_rent_for_exempt_for_account(self._conn)
        new_account_pk, txn, payer, new_account, opts = self._create_account_args(
            owner, skip_confirmation, balance_needed, self._conn.commitment
        )
        # Send the two instructions
        await self._conn.send_transaction(txn, payer, new_account, opts=opts, recent_blockhash=recent_blockhash)
        return new_account_pk

    async def create_associated_token_account(
        self,
        owner: PublicKey,
        skip_confirmation: bool = False,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> PublicKey:
        """Create an associated token account.

        Args:
            owner: User account that will own the associated token account.
            skip_confirmation: (optional) Option to skip transaction confirmation.

        Returns:
            Public key of the new associated account.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
        """
        # Construct transaction
        public_key, txn, payer, opts = self._create_associated_token_account_args(
            owner, skip_confirmation, self._conn.commitment
        )
        await self._conn.send_transaction(txn, payer, opts=opts, recent_blockhash=recent_blockhash)
        return public_key

    @staticmethod
    async def create_wrapped_native_account(
        conn: AsyncClient,
        program_id: PublicKey,
        owner: PublicKey,
        payer: Keypair,
        amount: int,
        skip_confirmation: bool = False,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> PublicKey:
        """Create and initialize a new account on the special native token mint.

        Args:
            conn: RPC connection to a solana cluster.
            program_id: SPL Token program account.
            owner: The owner of the new token account.
            payer: The source of the lamports to initialize, and payer of the initialization fees.
            amount: The amount of lamports to wrap.
            skip_confirmation: (optional) Option to skip transaction confirmation.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.

        Returns:
            The new token account.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
        """
        # Allocate memory for the account
        balance_needed = await AsyncToken.get_min_balance_rent_for_exempt_for_account(conn)
        new_account_public_key, txn, payer, new_account, opts = _TokenCore._create_wrapped_native_account_args(
            program_id, owner, payer, amount, skip_confirmation, balance_needed, conn.commitment
        )
        await conn.send_transaction(txn, payer, new_account, opts=opts, recent_blockhash=recent_blockhash)
        return new_account_public_key

    async def create_multisig(
        self,
        m: int,
        multi_signers: List[PublicKey],
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> PublicKey:  # pylint: disable=invalid-name
        """Create and initialize a new multisig.

        Args:
            m: Number of required signatures.
            multi_signers: Full set of signers.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.

        Returns:
            Public key of the new multisig account.
        """
        balance_needed = await AsyncToken.get_min_balance_rent_for_exempt_for_multisig(self._conn)
        txn, payer, multisig = self._create_multisig_args(m, multi_signers, balance_needed)
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        await self._conn.send_transaction(txn, payer, multisig, opts=opts_to_use, recent_blockhash=recent_blockhash)
        return multisig.public_key

    async def get_mint_info(self) -> MintInfo:
        """Retrieve mint information."""
        info = await self._conn.get_account_info(self.pubkey)
        return self._create_mint_info(info)

    async def get_account_info(self, account: PublicKey, commitment: Optional[Commitment] = None) -> AccountInfo:
        """Retrieve account information."""
        info = await self._conn.get_account_info(account, commitment)
        return self._create_account_info(info)

    async def transfer(
        self,
        source: PublicKey,
        dest: PublicKey,
        owner: Union[Keypair, PublicKey],
        amount: int,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Transfer tokens to another account.

        Args:
            source: Public key of account to transfer tokens from.
            dest: Public key of account to transfer tokens to.
            owner: Owner of the source account.
            amount: Number of tokens to transfer.
            multi_signers: (optional) Signing accounts if `owner` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._transfer_args(source, dest, owner, amount, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def approve(
        self,
        source: PublicKey,
        delegate: PublicKey,
        owner: PublicKey,
        amount: int,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Grant a third-party permission to transfer up the specified number of tokens from an account.

        Args:
            source: Public key of the source account.
            delegate: Account authorized to perform a transfer tokens from the source account.
            owner: Owner of the source account.
            amount: Maximum number of tokens the delegate may transfer.
            multi_signers: (optional) Signing accounts if `owner` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, payer, signers, opts = self._approve_args(source, delegate, owner, amount, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, payer, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def revoke(
        self,
        account: PublicKey,
        owner: PublicKey,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Revoke transfer authority for a given account.

        Args:
            account: Source account for which transfer authority is being revoked.
            owner: Owner of the source account.
            multi_signers: (optional) Signing accounts if `owner` is a multisig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, payer, signers, opts = self._revoke_args(account, owner, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, payer, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def set_authority(
        self,
        account: PublicKey,
        current_authority: Union[Keypair, PublicKey],
        authority_type: spl_token.AuthorityType,
        new_authority: Optional[PublicKey] = None,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Assign a new authority to the account.

        Args:
            account: Public key of the token account.
            current_authority: Current authority of the account.
            authority_type: Type of authority to set.
            new_authority: (optional) New authority of the account.
            multi_signers: (optional) Signing accounts if `owner` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, payer, signers, opts = self._set_authority_args(
            account, current_authority, authority_type, new_authority, multi_signers, opts_to_use
        )
        return await self._conn.send_transaction(txn, payer, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def mint_to(
        self,
        dest: PublicKey,
        mint_authority: Union[Keypair, PublicKey],
        amount: int,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Mint new tokens.

        Args:
            dest: Public key of the account to mint to.
            mint_authority: Public key of the minting authority.
            amount: Amount to mint.
            multi_signers: (optional) Signing accounts if `owner` is a multisig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.

        If skip confirmation is set to `False`, this method will block for at most 30 seconds
        or until the transaction is confirmed.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._mint_to_args(dest, mint_authority, amount, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def burn(
        self,
        account: PublicKey,
        owner: PublicKey,
        amount: int,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Burn tokens.

        Args:
            account: Account to burn tokens from.
            owner: Owner of the account.
            amount: Amount to burn.
            multi_signers: (optional) Signing accounts if `owner` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._burn_args(account, owner, amount, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def close_account(
        self,
        account: PublicKey,
        dest: PublicKey,
        authority: PublicKey,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Remove approval for the transfer of any remaining tokens.

        Args:
            account: Account to close.
            dest: Account to receive the remaining balance of the closed account.
            authority: Authority which is allowed to close the account.
            multi_signers: (optional) Signing accounts if `owner` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._close_account_args(account, dest, authority, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def freeze_account(
        self,
        account: PublicKey,
        authority: PublicKey,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Freeze account.

        Args:
            account: Account to freeze.
            authority: The mint freeze authority.
            multi_signers: (optional) Signing accounts if `authority` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._freeze_account_args(account, authority, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def thaw_account(
        self,
        account: PublicKey,
        authority: PublicKey,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Thaw account.

        Args:
            account: Account to thaw.
            authority: The mint freeze authority.
            multi_signers: (optional) Signing accounts if `authority` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._thaw_account_args(account, authority, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def transfer_checked(
        self,
        source: PublicKey,
        dest: PublicKey,
        owner: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Keypair]],
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Transfer tokens to another account, asserting the token mint and decimals.

        Args:
            source: Public key of account to transfer tokens from.
            dest: Public key of account to transfer tokens to.
            owner: Owner of the source account.
            amount: Number of tokens to transfer.
            decimals: Number of decimals in transfer amount.
            multi_signers: (optional) Signing accounts if `owner` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._transfer_checked_args(
            source, dest, owner, amount, decimals, multi_signers, opts_to_use
        )
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def approve_checked(
        self,
        source: PublicKey,
        delegate: PublicKey,
        owner: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Grant a third-party permission to transfer up the specified number of tokens from an account.

        This method also asserts the token mint and decimals.

        Args:
            source: Public key of the source account.
            delegate: Account authorized to perform a transfer tokens from the source account.
            owner: Owner of the source account.
            amount: Maximum number of tokens the delegate may transfer.
            decimals: Number of decimals in approve amount.
            multi_signers: (optional) Signing accounts if `owner` is a multisig.
            opts: (optional) Transaction options.
            recent_blockhash (optional): A prefetched blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, payer, signers, opts = self._approve_checked_args(
            source, delegate, owner, amount, decimals, multi_signers, opts_to_use
        )
        return await self._conn.send_transaction(txn, payer, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def mint_to_checked(
        self,
        dest: PublicKey,
        mint_authority: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Mint new tokens, asserting the token mint and decimals.

        Args:
            dest: Public key of the account to mint to.
            mint_authority: Public key of the minting authority.
            amount: Amount to mint.
            decimals: Number of decimals in amount to mint.
            multi_signers: (optional) Signing accounts if `owner` is a multiSig.
            opts: (optional) Transaction options.
            recent_blockhash (optional): A prefetched blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._mint_to_checked_args(
            dest, mint_authority, amount, decimals, multi_signers, opts_to_use
        )
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)

    async def burn_checked(
        self,
        account: PublicKey,
        owner: PublicKey,
        amount: int,
        decimals: int,
        multi_signers: Optional[List[Keypair]] = None,
        opts: Optional[TxOpts] = None,
        recent_blockhash: Optional[Blockhash] = None,
    ) -> RPCResponse:
        """Burn tokens, asserting the token mint and decimals.

        Args:
            account: Account to burn tokens from.
            owner: Owner of the account.
            amount: Amount to burn.
            decimals: Number of decimals in amount to burn.
            multi_signers: (optional) Signing accounts if `owner` is a multisig.
            opts: (optional) Transaction options.
            recent_blockhash: (optional) a prefetched Blockhash for the transaction.
        """
        opts_to_use = TxOpts(preflight_commitment=self._conn.commitment) if opts is None else opts
        txn, signers, opts = self._burn_checked_args(account, owner, amount, decimals, multi_signers, opts_to_use)
        return await self._conn.send_transaction(txn, *signers, opts=opts, recent_blockhash=recent_blockhash)
