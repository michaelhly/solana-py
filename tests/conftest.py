"""Fixtures for pytest."""

import os
import shutil
import time
from contextlib import suppress
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from solders.keypair import Keypair

from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from tests.validator_runtime import (
    ValidatorConfig,
    acquire_shared_validator,
    env_int,
    release_shared_validator,
    tail_file,
    validator_is_healthy,
)
from tests.utils import AIRDROP_AMOUNT, assert_valid_response

pytest_plugins = ["tests.fixture_accounts"]


@pytest.fixture(scope="session")
def solana_test_validator(worker_id: str) -> Generator[ValidatorConfig, None, None]:
    """Manage the lifecycle of solana-test-validator for the test session.

    The default mode uses a single shared validator process for all workers.
    Isolation is maintained at test-session level by using independent accounts
    and avoiding shared mutable test assumptions.

    Set ``SOLANA_VALIDATOR_EXTERNAL=1`` to opt in to using a pre-existing
    validator as-is.
    """
    if os.environ.get("SOLANA_VALIDATOR_EXTERNAL") == "1":
        rpc_url = os.environ.get("SOLANA_VALIDATOR_EXTERNAL_RPC_URL", "http://127.0.0.1:8899")
        ws_url = os.environ.get("SOLANA_VALIDATOR_EXTERNAL_WS_URL", "ws://127.0.0.1:8900")
        if not validator_is_healthy(rpc_url):
            pytest.skip(f"SOLANA_VALIDATOR_EXTERNAL=1 but no validator is reachable on {rpc_url}")
        yield ValidatorConfig(
            rpc_url=rpc_url,
            ws_url=ws_url,
            worker_id=worker_id,
            rpc_port=0,
            ledger_dir="",
        )
        return

    if not shutil.which("solana-test-validator"):
        pytest.skip("solana-test-validator not found in PATH; skipping integration tests")
        return
    config = acquire_shared_validator(worker_id)
    try:
        yield config
    finally:
        release_shared_validator()


@pytest.fixture(scope="session")
def validator_rpc_url(solana_test_validator: ValidatorConfig) -> str:
    """RPC URL for this test worker's validator."""
    return solana_test_validator.rpc_url


@pytest.fixture(scope="session")
def validator_ws_url(solana_test_validator: ValidatorConfig) -> str:
    """WS URL for this test worker's validator."""
    return solana_test_validator.ws_url


@pytest.fixture(scope="session")
def unit_test_http_client() -> Client:
    """Client to be used in unit tests."""
    client = Client(commitment=Processed)
    return client


@pytest.fixture(scope="session")
def unit_test_http_client_async() -> AsyncClient:
    """Async client to be used in unit tests."""
    client = AsyncClient(commitment=Processed)
    return client


@pytest.fixture(scope="session")
def test_http_client(
    solana_test_validator: ValidatorConfig,
    validator_rpc_url: str,
) -> Client:
    """Sync HTTP client pointed at the local test validator."""
    client = Client(endpoint=validator_rpc_url, commitment=Processed)
    # Wait until slot 5 is finalized so early-slot tests (e.g. get_block) pass
    timeout_secs = env_int("SOLANA_TEST_BLOCK_READY_TIMEOUT", 120)
    deadline = time.time() + timeout_secs
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            client.get_block(5)
            return client
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1)
    slot_debug = "unknown"
    block_height_debug = "unknown"
    with suppress(Exception):
        slot_debug = str(client.get_slot().value)
    with suppress(Exception):
        block_height_debug = str(client.get_block_height().value)
    log_tail = tail_file(Path(solana_test_validator.ledger_dir) / "validator.log")
    raise RuntimeError(
        "Validator did not finalize slot 5 within "
        f"{timeout_secs} s at {validator_rpc_url} "
        f"(worker={solana_test_validator.worker_id}, slot={slot_debug}, block_height={block_height_debug}).\n"
        f"last_error={last_error!r}\n"
        f"validator_log_tail:\n{log_tail}"
    )


@pytest.fixture(scope="module")
async def test_http_client_async(
    solana_test_validator: ValidatorConfig,
    validator_rpc_url: str,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client pointed at the local test validator."""
    http_client = AsyncClient(endpoint=validator_rpc_url, commitment=Processed)
    # Use a sync client for the readiness check so the async client's connection
    # pool is not seeded with connections tied to the setup event loop.
    sync_client = Client(endpoint=validator_rpc_url, commitment=Processed)
    deadline = time.time() + 15
    while time.time() < deadline:
        if sync_client.is_connected():
            break
        time.sleep(1)
    yield http_client
    await http_client.close()


@pytest.fixture(scope="function")
def random_funded_keypair(test_http_client: Client) -> Keypair:
    """A new keypair with some lamports."""
    kp = Keypair()
    resp = test_http_client.request_airdrop(kp.pubkey(), AIRDROP_AMOUNT)
    assert_valid_response(resp)
    test_http_client.confirm_transaction(resp.value)
    balance = test_http_client.get_balance(kp.pubkey())
    assert balance.value == AIRDROP_AMOUNT
    return kp
