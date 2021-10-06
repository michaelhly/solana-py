"""Unit tests for solana.system_program."""
import base64

import solana.system_program as sp
import solana.transaction as txlib
from solana.keypair import Keypair
from solana.publickey import PublicKey


def test_create_account():
    """Test creating a transaction for create account."""
    params = sp.CreateAccountParams(
        from_pubkey=Keypair().public_key,
        new_account_pubkey=Keypair().public_key,
        lamports=123,
        space=1,
        program_id=PublicKey(1),
    )
    assert sp.decode_create_account(sp.create_account(params)) == params


def test_transfer():
    """Test creating a transaction for transfer."""
    params = sp.TransferParams(from_pubkey=Keypair().public_key, to_pubkey=Keypair().public_key, lamports=123)
    assert sp.decode_transfer(sp.transfer(params)) == params


def test_assign():
    """Test creating a transaction for assign."""
    params = sp.AssignParams(
        account_pubkey=Keypair().public_key,
        program_id=PublicKey(1),
    )
    assert sp.decode_assign(sp.assign(params)) == params


def test_allocate():
    """Test creating a transaction for allocate."""
    params = sp.AllocateParams(
        account_pubkey=Keypair().public_key,
        space=12345,
    )
    assert sp.decode_allocate(sp.allocate(params)) == params


def test_allocate_with_seed():
    """Test creating a transaction for allocate with seed."""
    params = sp.AllocateWithSeedParams(
        account_pubkey=Keypair().public_key,
        base_pubkey=PublicKey(1),
        seed={"length": 4, "chars": "gqln"},
        space=65537,
        program_id=PublicKey(2),
    )
    assert sp.decode_allocate_with_seed(sp.allocate(params)) == params


def test_create_account_with_seed():
    """Test creating a an account with seed."""
    params = sp.CreateAccountWithSeedParams(
        from_pubkey=Keypair().public_key,
        new_account_pubkey=PublicKey(3),
        base_pubkey=PublicKey(1),
        seed={"length": 4, "chars": "gqln"},
        lamports=123,
        space=4,
        program_id=PublicKey(2),
    )
    assert sp.decode_create_account_with_seed(sp.create_account_with_seed(params)) == params


def test_create_nonce_account():
    from_keypair = Keypair.from_secret_key(
        bytes(
            [
                134,
                123,
                27,
                208,
                227,
                175,
                253,
                99,
                4,
                81,
                170,
                231,
                186,
                141,
                177,
                142,
                197,
                139,
                94,
                6,
                157,
                2,
                163,
                89,
                150,
                121,
                235,
                86,
                185,
                22,
                1,
                233,
                58,
                133,
                229,
                39,
                212,
                71,
                254,
                72,
                246,
                45,
                160,
                156,
                129,
                199,
                18,
                189,
                53,
                143,
                98,
                72,
                182,
                106,
                69,
                29,
                38,
                145,
                119,
                190,
                13,
                105,
                157,
                112,
            ]
        )
    )
    nonce_keypair = Keypair.from_secret_key(
        bytes(
            [
                139,
                81,
                72,
                75,
                252,
                57,
                73,
                247,
                63,
                130,
                201,
                76,
                183,
                43,
                60,
                197,
                65,
                154,
                28,
                240,
                134,
                0,
                232,
                108,
                61,
                123,
                56,
                26,
                35,
                201,
                13,
                39,
                188,
                128,
                179,
                175,
                136,
                5,
                89,
                185,
                92,
                183,
                175,
                131,
                56,
                53,
                228,
                11,
                20,
                34,
                138,
                148,
                51,
                27,
                205,
                76,
                75,
                148,
                184,
                34,
                74,
                129,
                238,
                225,
            ]
        )
    )

    wire_txn = base64.b64decode(
        b"AtZYPHSaLIQsFnHm4O7Lk0YdQRzovtsp0eKbKRPknDvZINd62tZaLPRzhm6N1LeINLzy31iHY6QE0bGW5c9aegu9g9SQqwsj"
        b"dKfNTYI0JLmzQd98HCUczjMM5H/gvGx+4k+sM/SreWkC3y1X+I1yh4rXehtVW5Sqo5nyyl7z88wOAgADBTqF5SfUR/5I9i2g"
        b"nIHHEr01j2JItmpFHSaRd74NaZ1wvICzr4gFWblct6+DODXkCxQiipQzG81MS5S4IkqB7uEGp9UXGSxWjuCKhF9z0peIzwNc"
        b"MUWyGrNE2AYuqUAAAAan1RcZLFxRIYzJTD1K8X9Y2u4Im6H9ROPb2YoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        b"AAAAAABXbYHxIfw3Z5Qq1LH8aj6Sj6LuqbCuwFhAmo21XevlfwIEAgABNAAAAACAhB4AAAAAAFAAAAAAAAAAAAAAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAwECAyQGAAAAOoXlJ9RH/kj2LaCcgccSvTWPYki2akUdJpF3vg1pnXA="
    )
    expected_txn = txlib.Transaction.deserialize(wire_txn)

    create_account_txn = sp.create_nonce_account(
        sp.CreateNonceAccountParams(
            from_pubkey=from_keypair.public_key,
            nonce_pubkey=nonce_keypair.public_key,
            authorized_pubkey=from_keypair.public_key,
            lamports=2000000,
        )
    )
    create_account_txn.recent_blockhash = "6tHKVLgLBEm25jaDsmatPTfoeHqSobTecJMESteTkPS6"

    create_account_hash = create_account_txn.serialize_message()

    create_account_txn.add_signature(from_keypair.public_key, from_keypair.sign(create_account_hash).signature)
    create_account_txn.add_signature(nonce_keypair.public_key, nonce_keypair.sign(create_account_hash).signature)

    assert create_account_txn == expected_txn


def test_advance_nonce_and_transfer():
    from_keypair = Keypair.from_secret_key(
        bytes(
            [
                134,
                123,
                27,
                208,
                227,
                175,
                253,
                99,
                4,
                81,
                170,
                231,
                186,
                141,
                177,
                142,
                197,
                139,
                94,
                6,
                157,
                2,
                163,
                89,
                150,
                121,
                235,
                86,
                185,
                22,
                1,
                233,
                58,
                133,
                229,
                39,
                212,
                71,
                254,
                72,
                246,
                45,
                160,
                156,
                129,
                199,
                18,
                189,
                53,
                143,
                98,
                72,
                182,
                106,
                69,
                29,
                38,
                145,
                119,
                190,
                13,
                105,
                157,
                112,
            ]
        )
    )
    nonce_keypair = Keypair.from_secret_key(
        bytes(
            [
                139,
                81,
                72,
                75,
                252,
                57,
                73,
                247,
                63,
                130,
                201,
                76,
                183,
                43,
                60,
                197,
                65,
                154,
                28,
                240,
                134,
                0,
                232,
                108,
                61,
                123,
                56,
                26,
                35,
                201,
                13,
                39,
                188,
                128,
                179,
                175,
                136,
                5,
                89,
                185,
                92,
                183,
                175,
                131,
                56,
                53,
                228,
                11,
                20,
                34,
                138,
                148,
                51,
                27,
                205,
                76,
                75,
                148,
                184,
                34,
                74,
                129,
                238,
                225,
            ]
        )
    )
    to_keypair = Keypair.from_secret_key(
        bytes(
            [
                56,
                246,
                74,
                56,
                168,
                158,
                189,
                97,
                126,
                149,
                175,
                70,
                23,
                14,
                251,
                206,
                172,
                69,
                61,
                247,
                39,
                226,
                8,
                68,
                97,
                159,
                11,
                196,
                212,
                57,
                2,
                1,
                252,
                124,
                54,
                3,
                18,
                109,
                223,
                27,
                225,
                28,
                59,
                202,
                49,
                248,
                244,
                17,
                165,
                33,
                101,
                59,
                217,
                79,
                234,
                217,
                251,
                85,
                9,
                6,
                40,
                0,
                221,
                10,
            ]
        )
    )

    wire_txn = base64.b64decode(
        b"Abh4hJNaP/IUJlHGpQttaGNWkjOZx71uLEnVpT0SBaedmThsTogjsh87FW+EHeuJrsZii+tJbrq3oJ5UYXPzXwwBAAIFOoXl"
        b"J9RH/kj2LaCcgccSvTWPYki2akUdJpF3vg1pnXC8gLOviAVZuVy3r4M4NeQLFCKKlDMbzUxLlLgiSoHu4fx8NgMSbd8b4Rw7"
        b"yjH49BGlIWU72U/q2ftVCQYoAN0KBqfVFxksVo7gioRfc9KXiM8DXDFFshqzRNgGLqlAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        b"AAAAAAAAAAAAAAAAAE13Mu8zaQSpG0zzGHpG62nK56DbGhuS4kXMF/ChHY1jAgQDAQMABAQAAAAEAgACDAIAAACAhB4AAAAA"
        b"AA=="
    )

    expected_txn = txlib.Transaction.deserialize(wire_txn)

    txn = txlib.Transaction(fee_payer=from_keypair.public_key)
    txn.recent_blockhash = "6DPp9aRRX6cLBqj5FepEvoccHFs3s8gUhd9t9ftTwAta"

    txn.add(
        sp.nonce_advance(
            sp.AdvanceNonceParams(
                nonce_pubkey=nonce_keypair.public_key,
                authorized_pubkey=from_keypair.public_key,
            )
        )
    )

    txn.add(
        sp.transfer(
            sp.TransferParams(from_pubkey=from_keypair.public_key, to_pubkey=to_keypair.public_key, lamports=2000000)
        )
    )

    txn_hash = txn.serialize_message()

    txn.add_signature(from_keypair.public_key, from_keypair.sign(txn_hash).signature)

    assert txn == expected_txn
