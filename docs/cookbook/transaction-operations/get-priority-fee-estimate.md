# Get Priority Fee Estimate

Learn how to estimate Solana priority fees using Helius's `getPriorityFeeEstimate` RPC extension through solana-py.

Helius extends the standard Solana JSON-RPC API with `getPriorityFeeEstimate`. solana-py does not define a dedicated model for that vendor-specific method, but its public `JsonRpcRequest` and `AsyncClient.send_rpc_request` APIs let you add strong request and response types without implementing an HTTP client.

Ref: https://www.helius.dev/docs/api-reference/priority-fee/getpriorityfeeestimate

## Code Example

```python
import asyncio
from enum import StrEnum
from typing import Literal, TypedDict

from pydantic import BaseModel, Field
from solana.rpc.async_api import AsyncClient
from solana.rpc.jsonrpc import JsonRpcRequest

HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key=YOUR_HELIUS_API_KEY"
TARGET_ACCOUNT = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"


class TransactionEncoding(StrEnum):
    """Transaction encodings accepted by Helius."""

    BASE58 = "Base58"
    BASE64 = "Base64"


class PriorityLevel(StrEnum):
    """Helius priority levels, ordered from cheapest to most aggressive."""

    MIN = "Min"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "VeryHigh"
    UNSAFE_MAX = "UnsafeMax"


# Request types are ordered from nested fields to the JSON-RPC envelope.
class PriorityFeeOptions(TypedDict, total=False):
    """Optional Helius controls, using the exact JSON field names."""

    transactionEncoding: TransactionEncoding
    priorityLevel: PriorityLevel
    includeAllPriorityFeeLevels: bool
    lookbackSlots: int
    includeVote: bool
    recommended: bool
    evaluateEmptySlotAsZero: bool


class PriorityFeeEstimateParams(TypedDict, total=False):
    """One parameter object accepted by getPriorityFeeEstimate."""

    transaction: str
    accountKeys: list[str]
    options: PriorityFeeOptions


class GetPriorityFeeEstimateRequest(JsonRpcRequest):
    """Bind solana-py's generic request model to the Helius method."""

    method: Literal["getPriorityFeeEstimate"] = "getPriorityFeeEstimate"
    params: list[PriorityFeeEstimateParams]


# Response types are ordered from nested data to the top-level result.
class PriorityFeeLevels(BaseModel):
    """Estimates for all levels when includeAllPriorityFeeLevels is true."""

    minimum: float = Field(alias="min")
    low: float
    medium: float
    high: float
    very_high: float = Field(alias="veryHigh")
    unsafe_max: float = Field(alias="unsafeMax")


class PriorityFeeEstimateResult(BaseModel):
    """The result object returned by Helius."""

    priority_fee_estimate: float | None = Field(default=None, alias="priorityFeeEstimate")
    priority_fee_levels: PriorityFeeLevels | None = Field(default=None, alias="priorityFeeLevels")


async def main() -> None:
    """Build, display, and send one strongly typed Helius RPC request."""
    # TypedDict checks this nested shape statically while keeping the payload
    # identical to the JSON documented by Helius.
    request = GetPriorityFeeEstimateRequest(
        params=[
            {
                # accountKeys makes the estimate reflect transactions that
                # lock this program/account instead of only global fee data.
                "accountKeys": [TARGET_ACCOUNT],
                "options": {"includeAllPriorityFeeLevels": True},
            },
        ],
    )

    print("Serialized request:")
    print(request.to_json(indent=2))
    print()
    # Keep credentials out of teaching material. Replace only this placeholder
    # before running the live request; no environment variable is consulted.
    if "YOUR_HELIUS_API_KEY" in HELIUS_RPC_URL:
        print("Replace YOUR_HELIUS_API_KEY in HELIUS_RPC_URL to send the request.")
        return

    async with AsyncClient(HELIUS_RPC_URL) as client:
        # send_rpc_request handles the JSON-RPC envelope and uses Pydantic's
        # TypeAdapter internally to validate the result as our custom model.
        result = await client.send_rpc_request(request, PriorityFeeEstimateResult)

    print("Response result:")
    print(result.model_dump_json(by_alias=True, exclude_none=True, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

## Explanation

1. **Bind the method with a `JsonRpcRequest` subclass** — `GetPriorityFeeEstimateRequest` locks `method` to the `"getPriorityFeeEstimate"` literal and types `params` as a list of `PriorityFeeEstimateParams`, so solana-py's generic request model is bound to the Helius method.
2. **TypedDict for request payloads** — `PriorityFeeOptions` and `PriorityFeeEstimateParams` mirror the exact JSON field names documented by Helius. This keeps the serialized wire payload identical while giving you static type checks on the nested shape.
3. **Pydantic models for the response** — `PriorityFeeLevels` and `PriorityFeeEstimateResult` use `Field(alias=...)` to map Helius's camelCase JSON keys (`priorityFeeEstimate`, `veryHigh`, `unsafeMax`) to snake_case Python attributes, with `model_dump_json(by_alias=True)` to round-trip them.
4. **Send with `AsyncClient.send_rpc_request`** — This API handles the JSON-RPC envelope (including the `jsonrpc` and `id` fields) and uses Pydantic's `TypeAdapter` internally to validate the result as your custom `PriorityFeeEstimateResult`, so no custom HTTP client is required.
5. **`accountKeys` for accurate estimates** — Passing the target account in `accountKeys` makes the estimate reflect transactions that lock that program/account instead of only global fee data. `includeAllPriorityFeeLevels: True` requests estimates for every priority level.
6. **Credential placeholder** — The example prints the serialized request and a hint instead of sending when the `YOUR_HELIUS_API_KEY` placeholder is still in `HELIUS_RPC_URL`, keeping credentials out of teaching material.
