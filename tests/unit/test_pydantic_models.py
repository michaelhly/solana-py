"""Tests for the Pydantic models that supersede the deprecated NamedTuple types."""

import pytest
from pydantic import ValidationError
from solders.keypair import Keypair

import solana.models as solana_models
import solana.rpc.models as rpc_models
import spl.memo.models as memo_models
import spl.token.models as token_models
from solana.rpc.commitment import Finalized
from solana.rpc.types import DataSliceOpts as DeprecatedDataSliceOpts
from solana.rpc.types import MemcmpOpts as DeprecatedMemcmpOpts
from solana.rpc.types import TokenAccountOpts as DeprecatedTokenAccountOpts
from solana.rpc.types import TxOpts as DeprecatedTxOpts
from solana.utils.cluster import ClusterUrls as DeprecatedClusterUrls
from solana.utils.cluster import Endpoint as DeprecatedEndpoint
from solana.vote_program import (
    WithdrawFromVoteAccountParams as DeprecatedWithdrawFromVoteAccountParams,
)
from spl.memo.instructions import MemoParams as DeprecatedMemoParams
from spl.token import instructions as token_instructions

# (deprecated NamedTuple, new Pydantic model) pairs that should be field-compatible.
_PARITY_PAIRS = [
    (DeprecatedDataSliceOpts, rpc_models.DataSliceOpts),
    (DeprecatedMemcmpOpts, rpc_models.MemcmpOpts),
    (DeprecatedTokenAccountOpts, rpc_models.TokenAccountOpts),
    (DeprecatedTxOpts, rpc_models.TxOpts),
    (DeprecatedClusterUrls, rpc_models.ClusterUrls),
    (DeprecatedEndpoint, rpc_models.Endpoint),
    (
        DeprecatedWithdrawFromVoteAccountParams,
        solana_models.WithdrawFromVoteAccountParams,
    ),
    (DeprecatedMemoParams, memo_models.MemoParams),
]

# All instruction params NamedTuples live in spl.token.instructions and are mirrored in spl.token.models.
_PARITY_PAIRS += [
    (getattr(token_instructions, name), getattr(token_models, name))
    for name in dir(token_instructions)
    if name.endswith("Params") and hasattr(token_models, name)
]


@pytest.mark.parametrize("deprecated_cls, model_cls", _PARITY_PAIRS, ids=lambda c: getattr(c, "__name__", c))
def test_field_parity(deprecated_cls, model_cls):
    """The new Pydantic model exposes the same field names, in order, as the deprecated NamedTuple."""
    assert list(model_cls.model_fields) == list(deprecated_cls._fields)


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
        rpc_models.MemcmpOpts(offset="not-an-int", bytes="3Mc6vR")


def test_field_descriptions_carried_over():
    """Attribute docstrings become field descriptions."""
    assert token_models.TransferParams.model_fields["program_id"].description == "SPL Token program account."


def test_from_namedtuple_converts_deprecated_instance():
    """from_namedtuple builds a model from a deprecated NamedTuple instance."""
    deprecated = DeprecatedMemcmpOpts(offset=4, bytes="3Mc6vR")
    model = rpc_models.MemcmpOpts.from_namedtuple(deprecated)
    assert isinstance(model, rpc_models.MemcmpOpts)
    assert model.offset == 4
    assert model.bytes == "3Mc6vR"


def test_from_namedtuple_preserves_defaults():
    """Defaulted fields survive conversion from a deprecated NamedTuple."""
    deprecated = DeprecatedTxOpts(skip_confirmation=False)
    model = rpc_models.TxOpts.from_namedtuple(deprecated)
    assert model.skip_confirmation is False
    assert model.preflight_commitment == Finalized
    assert model.max_retries is None


def test_from_namedtuple_is_idempotent():
    """from_namedtuple returns an existing model instance unchanged."""
    model = rpc_models.MemcmpOpts(offset=4, bytes="3Mc6vR")
    assert rpc_models.MemcmpOpts.from_namedtuple(model) is model


def test_from_namedtuple_converts_params_with_pubkeys():
    """A token params NamedTuple with Pubkey fields and a list default converts cleanly."""
    pubkey = Keypair().pubkey()
    deprecated = token_instructions.TransferParams(
        program_id=pubkey, source=pubkey, dest=pubkey, owner=pubkey, amount=7
    )
    model = token_models.TransferParams.from_namedtuple(deprecated)
    assert isinstance(model, token_models.TransferParams)
    assert model.amount == 7
    assert model.program_id == pubkey
    assert model.signers == []
