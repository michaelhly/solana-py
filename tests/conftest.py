"""Fixtures for pytest."""
import asyncio
from typing import NamedTuple

import pytest

from solana.blockhash import Blockhash
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed


class Clients(NamedTuple):
    """Container for http clients."""

    sync: Client
    async_: AsyncClient
    loop: asyncio.AbstractEventLoop


@pytest.fixture(scope="session")
def event_loop():
    """Event loop for pytest-asyncio."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def stubbed_blockhash() -> Blockhash:
    """Arbitrary block hash."""
    return Blockhash("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k")


@pytest.fixture(scope="session")
def stubbed_receiver() -> PublicKey:
    """Arbitrary known public key to be used as receiver."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")


@pytest.fixture(scope="session")
def stubbed_receiver_prefetched_blockhash() -> PublicKey:
    """Arbitrary known public key to be used as receiver."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i97")


@pytest.fixture(scope="session")
def stubbed_receiver_cached_blockhash() -> PublicKey:
    """Arbitrary known public key to be used as receiver."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i95")


@pytest.fixture(scope="session")
def async_stubbed_receiver() -> PublicKey:
    """Arbitrary known public key to be used as receiver."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i98")


@pytest.fixture(scope="session")
def async_stubbed_receiver_prefetched_blockhash() -> PublicKey:
    """Arbitrary known public key to be used as receiver."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i96")


@pytest.fixture(scope="session")
def async_stubbed_receiver_cached_blockhash() -> PublicKey:
    """Arbitrary known public key to be used as receiver."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i94")


@pytest.fixture(scope="session")
def stubbed_sender() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([8] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def stubbed_sender_prefetched_blockhash() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([9] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def stubbed_sender_cached_blockhash() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([4] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def stubbed_sender_for_token() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([2] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def async_stubbed_sender() -> Keypair:
    """Another arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([7] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def async_stubbed_sender_prefetched_blockhash() -> Keypair:
    """Another arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([5] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def async_stubbed_sender_cached_blockhash() -> Keypair:
    """Another arbitrary known account to be used as sender."""
    return Keypair.from_seed(bytes([3] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def freeze_authority() -> Keypair:
    """Arbitrary known account to be used as freeze authority."""
    return Keypair.from_seed(bytes([6] * PublicKey.LENGTH))


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


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client(docker_services) -> Client:
    """Test http_client.is_connected."""
    http_client = Client(commitment=Processed)
    docker_services.wait_until_responsive(timeout=15, pause=1, check=http_client.is_connected)
    return http_client


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client_cached_blockhash(docker_services) -> Client:
    """Test http_client.is_connected."""
    http_client = Client(commitment=Processed, blockhash_cache=True)
    docker_services.wait_until_responsive(timeout=15, pause=1, check=http_client.is_connected)
    return http_client


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client_async(docker_services, event_loop) -> AsyncClient:  # pylint: disable=redefined-outer-name
    """Test http_client.is_connected."""
    http_client = AsyncClient(commitment=Processed)

    def check() -> bool:
        return event_loop.run_until_complete(http_client.is_connected())

    docker_services.wait_until_responsive(timeout=15, pause=1, check=check)
    yield http_client
    event_loop.run_until_complete(http_client.close())


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client_async_cached_blockhash(
    docker_services, event_loop  # pylint: disable=redefined-outer-name
) -> AsyncClient:
    """Test http_client.is_connected."""
    http_client = AsyncClient(commitment=Processed, blockhash_cache=True)

    def check() -> bool:
        return event_loop.run_until_complete(http_client.is_connected())

    docker_services.wait_until_responsive(timeout=15, pause=1, check=check)
    yield http_client
    event_loop.run_until_complete(http_client.close())
