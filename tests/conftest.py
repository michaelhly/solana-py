"""Fixtures for pytest."""

import asyncio
import time
from typing import AsyncGenerator, NamedTuple

import pytest
from solders.hash import Hash as Blockhash
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from tests.utils import AIRDROP_AMOUNT, assert_valid_response

VALIDATOR_RPC_URL = "http://127.0.0.1:8899"
VALIDATOR_WS_URL = "ws://127.0.0.1:8900"


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
def test_http_client() -> Client:
    """Sync HTTP client pointed at the local test validator.

    Assumes solana-test-validator is already running on 127.0.0.1:8899.
    In CI this is started as a separate workflow step; locally run `make start-localnet`.
    """
    client = Client(endpoint=VALIDATOR_RPC_URL, commitment=Processed)
    # Wait until slot 5 is finalized so early-slot tests (e.g. get_block) pass
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            client.get_block(5)
            return client
        except Exception:  # noqa: BLE001
            time.sleep(1)
    raise RuntimeError(
        "Validator did not finalize slot 5 within 60 s — is solana-test-validator running on 127.0.0.1:8899?"
    )


@pytest.fixture(scope="module")
async def test_http_client_async() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client pointed at the local test validator."""
    http_client = AsyncClient(endpoint=VALIDATOR_RPC_URL, commitment=Processed)
    # Use a sync client for the readiness check so the async client's connection
    # pool is not seeded with connections tied to the setup event loop.
    sync_client = Client(endpoint=VALIDATOR_RPC_URL, commitment=Processed)
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
