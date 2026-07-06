# Add Priority Fees

Learn how to add priority fees to Solana transactions to increase the likelihood of faster processing during network congestion.

## Fee Structure Overview

A Solana transaction fee consists of two parts:

```text
total_fee = base_fee + prioritization_fee
```

- **Base fee**: 5,000 lamports per signature (50% burned, 50% to validator)
- **Prioritization fee**: optional, 100% to validator (none burned)

The prioritization fee is controlled by two Compute Budget instructions:

| Parameter              | Instruction              | Unit                | Description                                                                                                   |
| ---------------------- | ------------------------ | ------------------- |
| **Compute Unit Limit** | `set_compute_unit_limit` | CU                  | Maximum CUs the transaction may consume; the priority fee is charged against this **limit**, not actual usage |
| **Compute Unit Price** | `set_compute_unit_price` | micro-lamports / CU | Bid per CU; a **higher price means higher scheduling priority**                                               |

### Prioritization Fee Formula

```text
prioritization_fee = ceil(compute_unit_price × compute_unit_limit / 1,000,000)
```

> **Warning**: The prioritization fee is based on the **requested** CU limit, not the actual CU consumed. Setting a CU limit higher than needed means paying for unused compute units. Set the CU limit as close to the expected usage as possible.

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
    cu_limit = 10_000  # Max CUs (simple transfer needs ~1,500)
    cu_price = 5_000  # 5,000 micro-lamports per CU

    async with rpc:
        # Get latest blockhash
        latest_blockhash = await rpc.get_latest_blockhash()

        # Set CU limit: caps max compute units; fee is charged against this limit
        cu_limit_instruction = set_compute_unit_limit(cu_limit)

        # Set CU price: micro-lamports per CU; higher = higher scheduler priority
        cu_price_instruction = set_compute_unit_price(cu_price)

        # Create transfer instruction
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=recipient.pubkey(),
                lamports=amount,
            )
        )

        # Compute Budget instructions go before business instructions
        message = MessageV0.try_compile(
            payer=sender.pubkey(),
            instructions=[
                cu_limit_instruction,
                cu_price_instruction,
                transfer_instruction,
            ],
            address_lookup_table_accounts=[],
            recent_blockhash=latest_blockhash.value.blockhash,
        )

        # Create transaction
        transaction = VersionedTransaction(message, [sender])

        # Calculate estimated prioritization fee
        prioritization_fee_lamports = (cu_price * cu_limit) // 1_000_000

        print(f"Sender:             {sender.pubkey()}")
        print(f"Recipient:          {recipient.pubkey()}")
        print(f"Transfer:           {amount / 1_000_000_000} SOL")
        print(f"CU Limit:           {cu_limit}")
        print(f"CU Price:           {cu_price} micro-lamports/CU")
        print(f"Prioritization fee: {prioritization_fee_lamports} lamports")
        print("Transaction with priority fee created successfully")

if __name__ == "__main__":
    asyncio.run(main())
```

## Explanation

1. **`set_compute_unit_limit(units)`** — Sets the maximum CUs the transaction may consume. The prioritization fee is calculated against this limit, so keep it as close to expected usage as possible. A simple SOL transfer needs ~1,500 CU.
2. **`set_compute_unit_price(price)`** — Sets the bid per CU in micro-lamports. This directly determines scheduling priority; higher values make validators more likely to include your transaction first. Default is 0.
3. **Instruction ordering** — Compute Budget instructions must be placed **before** your business instructions.
4. **Fee calculation** — `prioritization_fee = ceil(CU price × CU limit / 1,000,000)`. Charged upfront whether the transaction succeeds or fails.

## Key Concepts

- **Compute Units (CU)**: Measure of on-chain computational resource consumption; a simple SOL transfer uses ~1,500 CU
- **CU Limit**: The maximum CU the transaction may consume; the prioritization fee is charged against this limit — setting it too high means paying for unused compute
- **CU Price**: Bid per CU in micro-lamports; higher values improve scheduling priority during congestion
- **Base fee**: 5,000 lamports per signature, 50% burned and 50% to the validator
- **Prioritization fee**: 100% goes to the validator (none burned)
- **Charged on failure**: Both base fee and prioritization fee are deducted even if the transaction fails
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

## Estimating the Right CU Limit

To avoid overpaying, set the CU limit close to what your transaction actually needs:

- Use `simulate_transaction()` to get the actual CU consumed, then set the limit slightly above that value
- See the [Optimize Compute Requested](./optimize-compute-requested.md) guide for a full simulation-based approach

## Priority Fee Strategies

- **Low priority**: CU price of 1–1,000 micro-lamports for non-urgent transactions
- **Medium priority**: CU price of 1,000–10,000 micro-lamports for time-sensitive transactions
- **High priority**: CU price of 10,000+ micro-lamports during network congestion

For real-time CU price estimates, use priority fee APIs from providers like Helius, QuickNode, or Triton.

## Benefits

- **Faster Processing**: Higher priority fees increase chances of faster inclusion
- **Congestion Management**: Helps during network congestion periods
- **MEV Protection**: Can help protect against MEV (Maximal Extractable Value) attacks
- **Predictable Costs**: Set known additional cost for transaction priority

Note: Priority fees are burned (destroyed) rather than going to validators, making them a deflationary mechanism.