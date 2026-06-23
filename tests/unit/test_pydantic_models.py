"""Tests for solana-py Pydantic models."""

from typing import cast

import pytest
from pydantic import ValidationError
from solders.keypair import Keypair

import solana.models as solana_models
import solana.rpc.models as rpc_models
import spl.memo.models as memo_models
import spl.token.models as token_models
from solana.rpc.commitment import Finalized


@pytest.mark.parametrize(
    "model_cls, expected_fields",
    [
        (rpc_models.DataSliceOpts, ["offset", "length"]),
        (rpc_models.MemcmpOpts, ["offset", "bytes"]),
        (rpc_models.TokenAccountOpts, ["mint", "program_id", "encoding", "data_slice"]),
        (
            rpc_models.TxOpts,
            [
                "skip_confirmation",
                "skip_preflight",
                "preflight_commitment",
                "max_retries",
                "last_valid_block_height",
            ],
        ),
        (rpc_models.ClusterUrls, ["devnet", "testnet", "mainnet_beta"]),
        (rpc_models.Endpoint, ["http", "https"]),
        (
            solana_models.WithdrawFromVoteAccountParams,
            ["vote_account_from_pubkey", "to_pubkey", "lamports", "withdrawer"],
        ),
        (memo_models.MemoParams, ["program_id", "signer", "message"]),
        (
            token_models.TransferParams,
            ["program_id", "source", "dest", "owner", "amount", "signers"],
        ),
    ],
)
def test_field_order(model_cls, expected_fields):
    """Critical model fields stay stable and ordered."""
    assert list(model_cls.model_fields) == expected_fields


def test_construction_and_attribute_access():
    """Models build from keyword args and expose attributes."""
    opts = rpc_models.MemcmpOpts(offset=4, bytes="3Mc6vR")
    assert opts.offset == 4
    assert opts.bytes == "3Mc6vR"


def test_defaults_preserved():
    """Defaults match the deprecated TxOpts."""
    opts = rpc_models.TxOpts()
    assert opts.skip_confirmation is True
    assert opts.skip_preflight is False
    assert opts.preflight_commitment == Finalized
    assert opts.max_retries is None
    assert opts.last_valid_block_height is None


def test_mutable_default_not_shared():
    """Each instance gets its own list for list-valued defaults."""
    pubkey = Keypair().pubkey()
    a = token_models.TransferParams(program_id=pubkey, source=pubkey, dest=pubkey, owner=pubkey, amount=1)
    b = token_models.TransferParams(program_id=pubkey, source=pubkey, dest=pubkey, owner=pubkey, amount=1)
    assert a.signers == []
    assert a.signers is not b.signers


def test_models_are_frozen():
    """Models are immutable, like the NamedTuples they replace."""
    opts = rpc_models.MemcmpOpts(offset=4, bytes="3Mc6vR")
    with pytest.raises(ValidationError):
        opts.offset = 5


def test_validation_rejects_bad_types():
    """Field validation is enforced."""
    with pytest.raises(ValidationError):
        rpc_models.MemcmpOpts(offset=cast(int, "not-an-int"), bytes="3Mc6vR")


def test_field_descriptions_carried_over():
    """Attribute docstrings become field descriptions."""
    assert token_models.TransferParams.model_fields["program_id"].description == "SPL Token program account."
