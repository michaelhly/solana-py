"""Fixtures for pytest"""
import pytest

from solanaweb3.account import Account
from solanaweb3.blockhash import Blockhash
from solanaweb3.publickey import PublicKey


@pytest.fixture(scope="session")
def test_blockhash() -> Blockhash:
    """Arbitrary block hash."""
    return Blockhash("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k")


@pytest.fixture(scope="session")
def test_reciever() -> PublicKey:
    """Arbitrary known public key to be used as reciever."""
    return PublicKey("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")


@pytest.fixture(scope="session")
def test_sender() -> Account:
    """Arbitrary known account to be used as sender."""
    return Account(bytes([8] * 32))
