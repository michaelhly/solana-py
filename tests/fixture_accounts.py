"""Deterministic account fixtures used across tests."""

import pytest
from solders.hash import Hash as Blockhash
from solders.keypair import Keypair
from solders.pubkey import Pubkey


def _seeded_keypair(seed_byte: int) -> Keypair:
    """Create a deterministic keypair from a repeated one-byte seed."""
    return Keypair.from_seed(bytes([seed_byte] * Pubkey.LENGTH))


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
    return _seeded_keypair(8)


@pytest.fixture(scope="session")
def stubbed_sender_prefetched_blockhash() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return _seeded_keypair(9)


@pytest.fixture(scope="session")
def stubbed_sender_for_token() -> Keypair:
    """Arbitrary known account to be used as sender."""
    return _seeded_keypair(2)


@pytest.fixture(scope="session")
def async_stubbed_sender() -> Keypair:
    """Another arbitrary known account to be used as sender."""
    return _seeded_keypair(7)


@pytest.fixture(scope="session")
def async_stubbed_sender_prefetched_blockhash() -> Keypair:
    """Another arbitrary known account to be used as sender."""
    return _seeded_keypair(5)


@pytest.fixture(scope="session")
def async_stubbed_sender_for_token() -> Keypair:
    """Arbitrary known account to be used as sender in async token tests."""
    return _seeded_keypair(3)


@pytest.fixture(scope="session")
def stubbed_sender_for_websockets() -> Keypair:
    """Arbitrary known account to be used as sender in websocket tests."""
    return _seeded_keypair(4)


@pytest.fixture(scope="session")
def freeze_authority() -> Keypair:
    """Arbitrary known account to be used as freeze authority."""
    return _seeded_keypair(6)
