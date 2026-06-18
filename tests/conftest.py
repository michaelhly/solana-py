"""Fixtures for pytest."""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import suppress
from pathlib import Path
from typing import AsyncGenerator, Generator, NamedTuple

import pytest
from solders.hash import Hash as Blockhash
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from tests.utils import AIRDROP_AMOUNT, assert_valid_response

_VALIDATOR_ARGS = [
    "--reset",
    "--rpc-pubsub-enable-vote-subscription",
    "--quiet",
]


class ValidatorConfig(NamedTuple):
    """Runtime configuration for a single validator instance."""

    rpc_url: str
    ws_url: str
    worker_id: str
    rpc_port: int
    ledger_dir: str


def _markexpr_includes_integration(markexpr: str) -> bool:
    """Return True when the current marker expression includes integration tests."""
    normalized = (markexpr or "").replace(" ", "")
    if not normalized:
        return True
    if "integration" not in normalized:
        return False
    return "notintegration" not in normalized


def pytest_xdist_auto_num_workers(config: pytest.Config) -> int | None:
    """Cap ``-n auto`` workers when integration tests are in scope.

    Running too many concurrent validator instances can exhaust host resources
    and cause startup failures (for example exit code 101). This hook keeps
    parallelism high while protecting stability.
    """
    markexpr = config.getoption("markexpr") or ""
    if not _markexpr_includes_integration(markexpr):
        return None

    cpu_count = os.cpu_count() or 1
    max_workers = int(os.environ.get("SOLANA_TEST_MAX_AUTO_WORKERS", "8"))
    return max(1, min(cpu_count, max_workers))


def _tail_file(path: Path, max_lines: int = 30) -> str:
    """Read the last few lines from a text file for error diagnostics."""
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-max_lines:])


def _worker_index(worker_id: str) -> int:
    """Map xdist worker id to a stable integer."""
    if worker_id == "master":
        return 0
    if worker_id.startswith("gw") and worker_id[2:].isdigit():
        return int(worker_id[2:])
    return 0


def _validator_is_healthy(rpc_url: str) -> bool:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getHealth"}).encode()
    try:
        req = urllib.request.Request(
            rpc_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read()).get("result") == "ok"
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture(scope="session")
def solana_test_validator(worker_id: str) -> Generator[ValidatorConfig, None, None]:
    """Manage the lifecycle of solana-test-validator for the test session.

    Under xdist, each worker gets its own validator process, ledger dir, and
    RPC/WS ports, which enables safe parallel integration tests.

    Set ``SOLANA_VALIDATOR_EXTERNAL=1`` to opt in to using a pre-existing
    validator as-is. This mode is not isolated across workers and therefore is
    only supported when not using xdist parallel workers.
    """
    worker_count = int(os.environ.get("PYTEST_XDIST_WORKER_COUNT", "1"))
    if os.environ.get("SOLANA_VALIDATOR_EXTERNAL") == "1":
        if worker_count > 1:
            pytest.skip(
                "SOLANA_VALIDATOR_EXTERNAL=1 does not support xdist isolation; run with -n 1"
            )
        rpc_url = os.environ.get(
            "SOLANA_VALIDATOR_EXTERNAL_RPC_URL", "http://127.0.0.1:8899"
        )
        ws_url = os.environ.get(
            "SOLANA_VALIDATOR_EXTERNAL_WS_URL", "ws://127.0.0.1:8900"
        )
        if not _validator_is_healthy(rpc_url):
            pytest.skip(
                f"SOLANA_VALIDATOR_EXTERNAL=1 but no validator is reachable on {rpc_url}"
            )
        yield ValidatorConfig(
            rpc_url=rpc_url,
            ws_url=ws_url,
            worker_id=worker_id,
            rpc_port=0,
            ledger_dir="",
        )
        return

    if not shutil.which("solana-test-validator"):
        pytest.skip(
            "solana-test-validator not found in PATH; skipping integration tests"
        )
        return

    index = _worker_index(worker_id)
    base_rpc_port = int(os.environ.get("SOLANA_TEST_VALIDATOR_BASE_RPC_PORT", "18899"))
    rpc_port = base_rpc_port + (index * 2)
    ws_port = rpc_port + 1
    rpc_url = f"http://127.0.0.1:{rpc_port}"
    ws_url = f"ws://127.0.0.1:{ws_port}"
    ledger_dir = tempfile.mkdtemp(prefix=f"solana-test-ledger-{worker_id}-")
    validator_log_path = Path(ledger_dir) / "validator.log"
    dynamic_port_start = 20000 + (index * 100)
    gossip_port = 23000 + (index * 100)
    faucet_port = 24000 + (index * 100)
    validator_args = [
        "solana-test-validator",
        *_VALIDATOR_ARGS,
        "--ledger",
        ledger_dir,
        "--rpc-port",
        str(rpc_port),
        "--gossip-port",
        str(gossip_port),
        "--faucet-port",
        str(faucet_port),
        "--dynamic-port-range",
        f"{dynamic_port_start}-{dynamic_port_start + 99}",
    ]

    with validator_log_path.open("w", encoding="utf-8") as validator_log:
        proc = subprocess.Popen(
            validator_args,
            stdout=validator_log,
            stderr=validator_log,
        )

        deadline = time.time() + 60
        while time.time() < deadline:
            if _validator_is_healthy(rpc_url):
                break
            if proc.poll() is not None:
                log_tail = _tail_file(validator_log_path)
                raise RuntimeError(
                    "solana-test-validator exited prematurely "
                    f"(code {proc.returncode}) for worker {worker_id} at {rpc_url}.\n"
                    f"args={validator_args}\n"
                    f"log_tail:\n{log_tail}"
                )
            time.sleep(1)
        else:
            proc.terminate()
            proc.wait(timeout=10)
            log_tail = _tail_file(validator_log_path)
            raise RuntimeError(
                f"solana-test-validator did not become healthy within 60 s at {rpc_url}.\n"
                f"args={validator_args}\n"
                f"log_tail:\n{log_tail}"
            )

    yield ValidatorConfig(
        rpc_url=rpc_url,
        ws_url=ws_url,
        worker_id=worker_id,
        rpc_port=rpc_port,
        ledger_dir=ledger_dir,
    )

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    shutil.rmtree(ledger_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def validator_rpc_url(solana_test_validator: ValidatorConfig) -> str:
    """RPC URL for this test worker's validator."""
    return solana_test_validator.rpc_url


@pytest.fixture(scope="session")
def validator_ws_url(solana_test_validator: ValidatorConfig) -> str:
    """WS URL for this test worker's validator."""
    return solana_test_validator.ws_url


class Clients(NamedTuple):
    """Container for http clients."""

    sync: Client
    async_: AsyncClient
    loop: asyncio.AbstractEventLoop


@pytest.fixture(scope="session")
def stubbed_blockhash() -> Blockhash:
    """Arbitrary block hash."""
    return Blockhash.from_string("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k")


@pytest.fixture(scope="session")
def stubbed_receiver() -> Pubkey:
    """Arbitrary known public key to be used as receiver."""
    return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")


@pytest.fixture(scope="session")
def stubbed_receiver_prefetched_blockhash() -> Pubkey:
    """Arbitrary known public key to be used as receiver."""
    return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i97")


@pytest.fixture(scope="session")
def async_stubbed_receiver() -> Pubkey:
    """Arbitrary known public key to be used as receiver."""
    return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i98")


@pytest.fixture(scope="session")
def async_stubbed_receiver_prefetched_blockhash() -> Pubkey:
    """Arbitrary known public key to be used as receiver."""
    return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i96")


@pytest.fixture(scope="session")
def stubbed_sender() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([8] * Pubkey.LENGTH))


@pytest.fixture(scope="session")
def stubbed_sender_prefetched_blockhash() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([9] * Pubkey.LENGTH))


@pytest.fixture(scope="session")
def stubbed_sender_for_token() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([2] * Pubkey.LENGTH))


@pytest.fixture(scope="session")
def async_stubbed_sender() -> Keypair:
    """Another arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([7] * Pubkey.LENGTH))


@pytest.fixture(scope="session")
def async_stubbed_sender_prefetched_blockhash() -> Keypair:
    """Another arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([5] * Pubkey.LENGTH))


@pytest.fixture(scope="session")
def async_stubbed_sender_for_token() -> Keypair:
    """Arbitrary known account to be used as sender in async token tests."""
    return Keypair.from_seed(bytes([3] * Pubkey.LENGTH))


@pytest.fixture(scope="session")
def stubbed_sender_for_websockets() -> Keypair:
    """Arbitrary known account to be used as sender in websocket tests."""
    return Keypair.from_seed(bytes([4] * Pubkey.LENGTH))


@pytest.fixture(scope="session")
def freeze_authority() -> Keypair:
    """Arbitrary known account to be used as freeze authority."""
    return Keypair.from_seed(bytes([6] * Pubkey.LENGTH))


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
    timeout_secs = int(os.environ.get("SOLANA_TEST_BLOCK_READY_TIMEOUT", "120"))
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
    log_tail = _tail_file(Path(solana_test_validator.ledger_dir) / "validator.log")
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
