"""Fixtures for pytest."""
import pytest

from solana.account import Account
from solana.blockhash import Blockhash
from solana.publickey import PublicKey
from solana.rpc.api import Client


@pytest.fixture(scope="session")
def stubbed_blockhash() -> Blockhash:
    """Arbitrary block hash."""
    return Blockhash("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k")


@pytest.fixture(scope="session")
def stubbed_reciever() -> PublicKey:
    """Arbitrary known public key to be used as reciever."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")


@pytest.fixture(scope="session")
def stubbed_sender() -> Account:
    """Arbitrary known account to be used as sender."""
    return Account(bytes([8] * PublicKey.LENGTH))


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_http_client(docker_services) -> Client:
    """Test http_client.is_connected."""
    http_client = Client()
    docker_services.wait_until_responsive(timeout=15, pause=1, check=http_client.is_connected)
    return http_client
