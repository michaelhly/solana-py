# Add Priority Fees

Learn how to add priority fees to Solana transactions to increase the likelihood of faster processing during network congestion.

## Two Key Parameters

Solana uses two parameters from the **Compute Budget Program** to control transaction priority:

| Parameter              | Instruction              | Unit                | Description                                                                              |
| ---------------------- | ------------------------ | ------------------- | ---------------------------------------------------------------------------------------- |
| **Compute Unit Limit** | `set_compute_unit_limit` | CU (Compute Units)  | Caps the **maximum** compute units the transaction can consume, preventing runaway costs |
| **Compute Unit Price** | `set_compute_unit_price` | micro-lamports / CU | The additional fee paid per compute unit; a **higher price means higher priority**       |

In short:
- **CU Limit** = sets a ceiling on how much compute you can use → prevents "budget blowout"
- **CU Price** = how much you bid per CU → higher bids get picked up by validators first

> By default, each transaction can use up to **200,000 CU**. For simple transactions (e.g., a basic SOL transfer uses ~1,500 CU), setting a higher CU Limit does **not** cost more — you only pay for what's actually consumed. However, setting the CU Limit too low will cause the transaction to fail.

## Code Example

```python
#!/usr/bin/env python3
"""
Solana Cookbook - How to Add Priority Fees to a Transaction
"""

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.system_program import transfer, TransferParams
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price

async def main():
    rpc = AsyncClient("https://api.devnet.solana.com")

    sender = Keypair()
    recipient = Keypair()

    amount = 1_000_000_000  # 1 SOL

    # ---- Priority fee parameters ----
    cu_limit = 10_000  # Cap compute units at 10,000
    cu_price = 5_000  # Bid 5,000 micro-lamports per CU

    async with rpc:
        # Get latest blockhash
        latest_blockhash = await rpc.get_latest_blockhash()

        # (1) Set CU limit: cap the max compute units this transaction can use
        cu_limit_instruction = set_compute_unit_limit(cu_limit)

        # (2) Set CU price: the tip per CU; higher = higher priority
        cu_price_instruction = set_compute_unit_price(cu_price)

        # Create transfer instruction
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=recipient.pubkey(),
                lamports=amount,
            )
        )

        # Compute Budget instructions must come first
        message = MessageV0.try_compile(
            payer=sender.pubkey(),
            instructions=[
                cu_limit_instruction,   # CU limit first
                cu_price_instruction,   # CU price second
                transfer_instruction,   # business instruction last
            ],
            address_lookup_table_accounts=[],
            recent_blockhash=latest_blockhash.value.blockhash,
        )

        # Create transaction
        transaction = VersionedTransaction(message, [sender])

        print(f"Sender:       {sender.pubkey()}")
        print(f"Recipient:    {recipient.pubkey()}")
        print(f"Transfer:     {amount / 1_000_000_000} SOL")
        print(f"CU Limit:     {cu_limit}")
        print(f"CU Price:     {cu_price} micro-lamports/CU")
        print(f"Max Fee:      ~{cu_limit * cu_price / 1_000_000:.2f} SOL (limit × price)")
        print("Transaction with priority fee created successfully")

if __name__ == "__main__":
    asyncio.run(main())
```

## Explanation

1. **`set_compute_unit_limit(units)`** — Caps how many compute units this transaction can consume, preventing extreme fees if execution behaves unexpectedly
2. **`set_compute_unit_price(price)`** — Sets the priority fee bid per CU (in micro-lamports); higher bids make validators more likely to include your transaction first
3. **Instruction ordering** — Compute Budget instructions must be placed **before** your business instructions
4. **Actual cost** — The final priority fee = actual CU consumed × CU Price (not CU Limit × CU Price); setting a high CU Limit does **not** increase your cost

## Key Concepts

- **Compute Units (CU)**: Measure of on-chain computational resource consumption; a simple SOL transfer consumes ~1,500 CU
- **CU Limit**: The maximum CU this transaction is allowed to consume; prevents runaway costs from unexpected execution paths
- **CU Price**: The "tip" per CU, denominated in micro-lamports; higher values improve transaction landing during congestion
- **Actual billing**: You pay actual CU consumed × CU Price, not Limit × Price
- **Default limit**: Without explicit setting, the default cap is 200,000 CU per transaction; simple transfers typically use far less
- **Instruction ordering**: Compute Budget instructions must always appear before business instructions

## Usage

To run this example:

1. Install required dependencies:
   ```bash
   pip install solana-py solders
   ```

2. Run the script:
   ```bash
   python add_priority_fees.py
   ```

## Priority Fee Strategies

Different scenarios for priority fees:

- **Low Priority**: 0-1000 lamports for standard transactions
- **Medium Priority**: 1000-5000 lamports for time-sensitive transactions
- **High Priority**: 5000+ lamports for urgent transactions during congestion

## Benefits

- **Faster Processing**: Higher priority fees increase chances of faster inclusion
- **Congestion Management**: Helps during network congestion periods
- **MEV Protection**: Can help protect against MEV (Maximal Extractable Value) attacks
- **Predictable Costs**: Set known additional cost for transaction priority

Note: Priority fees are burned (destroyed) rather than going to validators, making them a deflationary mechanism.