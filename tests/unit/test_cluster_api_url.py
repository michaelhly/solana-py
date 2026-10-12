"""Test cluster_api_url."""

from solana.utils.cluster import cluster_api_url


def test_input_output():
    """Test that cluster_api_url generates the expected output."""
    assert cluster_api_url() == "https://api.devnet.solana.com"
    assert cluster_api_url("devnet") == "https://api.devnet.solana.com"
    assert cluster_api_url("devnet", True) == "https://api.devnet.solana.com"
    assert cluster_api_url("devnet", False) == "http://api.devnet.solana.com"
    assert cluster_api_url("testnet") == "https://api.testnet.solana.com"
    assert cluster_api_url("testnet", False) == "http://api.testnet.solana.com"


def test_mainnet():
    """Test that the mainnet cluster resolves to its URL."""
    assert cluster_api_url("mainnet") == "https://api.mainnet.solana.com/"
    assert cluster_api_url("mainnet", True) == "https://api.mainnet.solana.com/"
    assert cluster_api_url("mainnet", False) == "http://api.mainnet.solana.com/"
