"""Fixtures for pytest."""
import asyncio
from typing import NamedTuple

import pytest

from solana.account import Account
from solana.blockhash import Blockhash
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient


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
    """Arbitrary known public key to be used as reciever."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")


@pytest.fixture(scope="session")
def alt_stubbed_receiver() -> PublicKey:
    """Arbitrary known public key to be used as reciever."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i98")


@pytest.fixture(scope="session")
def stubbed_sender() -> Account:
    """Arbitrary known account to be used as sender."""
    return Account(bytes([8] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def alt_stubbed_sender() -> Account:
    """Another arbitrary known account to be used as sender."""
    return Account(bytes([7] * PublicKey.LENGTH))


@pytest.fixture(scope="session")
def freeze_authority() -> Account:
    """Arbitrary known account to be used as freeze authority."""
    return Account(bytes([6] * PublicKey.LENGTH))


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client(docker_services) -> Client:
    """Test http_client.is_connected."""
    http_client = Client()
    docker_services.wait_until_responsive(timeout=15, pause=1, check=http_client.is_connected)
    return http_client


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client_async(docker_services, event_loop) -> AsyncClient:  # pylint: disable=redefined-outer-name
    """Test http_client.is_connected."""
    http_client = AsyncClient()

    def check() -> bool:
        return event_loop.run_until_complete(http_client.is_connected())

    docker_services.wait_until_responsive(timeout=15, pause=1, check=check)
    yield http_client
    event_loop.run_until_complete(http_client.close())


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_clients(docker_services) -> Clients:
    """Test http_client.is_connected."""
    http_client = Client()
    async_client = AsyncClient()
    loop = asyncio.get_event_loop()

    def check() -> bool:
        sync_result = http_client.is_connected()
        async_result = loop.run_until_complete(async_client.is_connected())
        return sync_result and async_result

    docker_services.wait_until_responsive(timeout=15, pause=1, check=check)
    clients = Clients(sync=http_client, async_=async_client, loop=loop)
    yield clients

    clients.loop.run_until_complete(async_client.close())
