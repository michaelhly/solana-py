"""Tests for commitment helpers."""

import pytest

from solana.rpc.commitment import Commitment, commitment_comparator


@pytest.mark.parametrize("commitment", list(Commitment))
def test_commitment_comparator_equal_plain_str(commitment: Commitment):
    """A plain string such as "confirmed" equals its Commitment member."""
    plain = "".join(commitment.value)  # a str object that is not the enum member
    assert commitment_comparator(plain, commitment) == 0
    assert commitment_comparator(commitment, plain) == 0
    assert commitment_comparator(plain, "".join(commitment.value)) == 0
