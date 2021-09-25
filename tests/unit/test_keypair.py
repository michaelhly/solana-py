import base64

from nacl.bindings import crypto_box_PUBLICKEYBYTES

from solana.keypair import Keypair


def test_new_keypair() -> None:
    """Test new keypair with random seed is created successfully."""
    keypair = Keypair()
    assert len(keypair.secret_key) == 64
    assert len(bytes(keypair.public_key)) == crypto_box_PUBLICKEYBYTES


def test_generate_keypair() -> None:
    """Test .generate constructor works."""
    keypair = Keypair.generate()
    assert len(keypair.secret_key) == 64


def test_create_from_secret_key() -> None:
    """Test creation with 64-byte secret key."""
    secret_key = base64.b64decode(
        "mdqVWeFekT7pqy5T49+tV12jO0m+ESW7ki4zSU9JiCgbL0kJbj5dvQ/PqcDAzZLZqzshVEs01d1KZdmLh4uZIg=="
    )
    keypair = Keypair.from_secret_key(secret_key)
    assert str(keypair.public_key) == "2q7pyhPwAwZ3QMfZrnAbDhnh9mDUqycszcpf86VgQxhF"
    assert keypair.secret_key == secret_key


def test_create_from_seed() -> None:
    """Test creation with 32-byte secret seed."""
    seed = bytes([8] * 32)
    keypair = Keypair.from_seed(seed)
    assert str(keypair.public_key) == "2KW2XRd9kwqet15Aha2oK3tYvd3nWbTFH1MBiRAv1BE1"
    assert keypair.seed == seed
