# Create PDA Account

This example shows how to derive a Program Derived Address (PDA) on Solana and how an account at that address gets created.

!!! note "Only the owning program can create an account at a PDA"
    A PDA has no private key, so a client transaction can't sign for it and can't create an account there through the System Program. The program the PDA belongs to creates the account itself: it makes a cross-program invocation (CPI) to the System Program's `create_account` and signs for the PDA with `invoke_signed`, using the PDA's seeds and bump. The client derives the same address and passes it in the accounts of that program's instruction.

The code below derives the PDA and then uses `create_account_with_seed` to create an account at an address derived with a seed (not a PDA), which the payer can sign for.

## Code

```python
#!/usr/bin/env python3
"""
Solana Cookbook - How to Create a PDA's Account
"""

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import create_account_with_seed, CreateAccountWithSeedParams
from solders.transaction import VersionedTransaction
from solders.message import MessageV0


async def main():
    rpc = AsyncClient("https://api.devnet.solana.com")

    payer = Keypair()
    program_id = Pubkey.from_string("11111111111111111111111111111111")

    # Create PDA (Program Derived Address)
    # Only program_id can create an account here, via invoke_signed
    seed = "hello"
    pda, bump = Pubkey.find_program_address([seed.encode()], program_id)

    # Address derived with a seed (not a PDA) that the payer can create
    account_with_seed = Pubkey.create_with_seed(payer.pubkey(), seed, program_id)

    space = 100  # Account data space

    async with rpc:
        # Get minimum balance for rent exemption
        rent_lamports = await rpc.get_minimum_balance_for_rent_exemption(space)

        # Get latest blockhash
        recent_blockhash = await rpc.get_latest_blockhash()

        # Use the payer as base for seed derivation
        create_account_instruction = create_account_with_seed(
            CreateAccountWithSeedParams(
                from_pubkey=payer.pubkey(),
                to_pubkey=account_with_seed,
                base=payer.pubkey(),
                seed=seed,
                lamports=rent_lamports.value,
                space=space,
                owner=program_id,
            )
        )

        # Create message
        message = MessageV0.try_compile(
            payer=payer.pubkey(),
            instructions=[create_account_instruction],
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash.value.blockhash,
        )

        # Create transaction
        transaction = VersionedTransaction(message, [payer])

        print(f"Payer: {payer.pubkey()}")
        print(f"PDA: {pda}")
        print(f"Account with seed: {account_with_seed}")
        print(f"Seed: {seed}")
        print(f"Bump: {bump}")
        print(f"Space: {space} bytes")
        print(f"Rent Lamports: {rent_lamports.value}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Explanation

1. **Find PDA**: Use `find_program_address()` to derive the PDA and bump from a seed and program ID
2. **Derive address with seed**: Use `Pubkey.create_with_seed()` with the payer as base. The System Program rejects any other `to_pubkey` with `AddressWithSeedMismatch`
3. **Calculate rent**: Get the minimum balance required for the account size
4. **Create instruction**: Build the `create_account_with_seed` instruction for the address with seed. The payer signs as base
5. **Build transaction**: Compile the instruction into a transaction

## PDA vs. address with seed

The same seed and program ID give two different addresses:

=== "find_program_address"

    ```python
    program_id = Pubkey.from_string("11111111111111111111111111111111")

    pda, bump = Pubkey.find_program_address([b"hello"], program_id)
    # pda:  2PjSSVURwJV4o9wz1BDVwwddvcUCuF1NKFpcQBF9emYJ
    # bump: 255
    ```

=== "create_with_seed"

    ```python
    program_id = Pubkey.from_string("11111111111111111111111111111111")
    base = Pubkey.from_string("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")

    address = Pubkey.create_with_seed(base, "hello", program_id)
    # address: D1atEcWrBvdyho5xp33jnw6jdJL1va87fzxr98jFeA9M
    ```

A PDA is searched for with a bump until it lands off the ed25519 curve, so it has no private key and only the program can sign for it with `invoke_signed`; an address with seed is `sha256(base || seed || owner)`, and the `base` keypair must sign to create it.

## Key Concepts

- **PDA**: Program Derived Address - a deterministic address derived from seeds
- **Seed**: A string used to derive the PDA address
- **Bump**: A value that ensures the PDA is not on the ed25519 curve
- **Program ID**: The program that will own the PDA account
- **Deterministic**: The same seed always produces the same PDA

## Usage

```bash
python create_pda_account.py
```

This will output:
```
Payer: 5J8...abc
PDA: 2PjSSVURwJV4o9wz1BDVwwddvcUCuF1NKFpcQBF9emYJ
Account with seed: 7Gh...xyz
Seed: hello
Bump: 255
Space: 100 bytes
Rent Lamports: 1158240
```

## Use Cases

- **Program state**: Store program-specific data
- **Token accounts**: Create token accounts owned by programs
- **Cross-program invocation**: Allow programs to sign for their PDAs with `invoke_signed`
