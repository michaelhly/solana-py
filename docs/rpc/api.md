# Migrating from Client API to AsyncClient API

`Client` was deprecated. `AsyncClient` is now the supported RPC client in `solana-py`.

## Why `Client` was removed

Recent releases moved the RPC stack to a single async implementation.

This keeps the library smaller and removes duplicate sync and async request paths. It also keeps new RPC features on one supported client surface instead of maintaining two parallel implementations.

The async RPC stack also supports transport behavior that is useful for RPC-heavy applications:

- request rate limiting with `rate_limit`
- persistent HTTP connections
- HTTP/2 support
- transport retries

In the current codebase, these features live on `AsyncClient` and `AsyncHTTPProvider`.

## Minimal migration

For most applications, the migration is:

1. Replace imports from `solana.rpc.api` with `solana.rpc.async_api`.
2. Replace `Client(...)` with `AsyncClient(...)`.
3. Move RPC calls into `async def` functions and `await` the client methods.
4. Keep a small sync wrapper only at the application boundary when the rest of the code is still synchronous.

If you imported the removed sync provider directly, replace `solana.rpc.providers.http.HTTPProvider` with `solana.rpc.async_http_provider.AsyncHTTPProvider`.

## Minimal sync adaptation

If your environment already supports async code, use `AsyncClient` directly and keep the call path async end to end.

```python
import asyncio

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

RPC_URL = "https://api.mainnet-beta.solana.com"


async def get_balance(pubkey: Pubkey) -> int:
    async with AsyncClient(RPC_URL, rate_limit=20) as client:
        response = await client.get_balance(pubkey)
        return response.value


def get_balance_sync(pubkey: Pubkey) -> int:
    return asyncio.run(get_balance(pubkey))
```

This is the preferred shape for async applications and for deployments where an async server is already available. Async I/O usually gives better throughput for RPC-heavy workloads with less overhead than thread-based concurrency.

If you are tied to synchronous framework code and cannot move the request path to an async server yet, `asgiref.sync.async_to_sync` is often the better adapter.

### Django code migration

For Django, you can use this approach with a proxy function that applies `async_to_sync()` to the coroutine

```python
from asgiref.sync import async_to_sync
from django.http import JsonResponse

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

RPC_URL = "https://api.mainnet-beta.solana.com"


class SolanaService:
    async def aget_balance(self, pubkey: Pubkey) -> int:
        async with AsyncClient(RPC_URL, rate_limit=20) as client:
            response = await client.get_balance(pubkey)
            return response.value

    def get_balance(self, pubkey: Pubkey) -> int:
        return async_to_sync(self.aget_balance)(pubkey)


solana_service = SolanaService()


def wallet_balance_view(request, wallet_address: str):
    pubkey = Pubkey.from_string(wallet_address)
    lamports = solana_service.get_balance(pubkey)
    return JsonResponse({"lamports": lamports})
```

### Flask code migration

For Flask-style synchronous applications, the same pattern applies:

```python
from asgiref.sync import async_to_sync
from flask import Flask, jsonify

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

app = Flask(__name__)
RPC_URL = "https://api.mainnet-beta.solana.com"


class SolanaService:
    async def aget_balance(self, pubkey: Pubkey) -> int:
        async with AsyncClient(RPC_URL, rate_limit=20) as client:
            response = await client.get_balance(pubkey)
            return response.value

    def get_balance(self, pubkey: Pubkey) -> int:
        return async_to_sync(self.aget_balance)(pubkey)


solana_service = SolanaService()


@app.get("/wallet/<wallet_address>/balance")
def wallet_balance(wallet_address: str):
    pubkey = Pubkey.from_string(wallet_address)
    lamports = solana_service.get_balance(pubkey)
    return jsonify({"lamports": lamports})
```

## What changes in application code

The RPC method names are the same, but calls must now be awaited.

Before:

```python
response = client.get_balance(pubkey)
lamports = response.value
```

After:

```python
response = await client.get_balance(pubkey)
lamports = response.value
```

The same rule applies to other RPC methods such as `get_account_info`, `get_latest_blockhash`, `send_transaction`, and `simulate_transaction`.

## Closing the client

`AsyncClient` should be closed when you are done with it.

Use one of these patterns:

- `async with AsyncClient(...) as client:`
- `await client.close()`

This is the main lifecycle change for code that previously relied on the removed synchronous client.
