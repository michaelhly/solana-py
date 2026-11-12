"""Tests for the new solana.spl.memo client."""

import pytest
from solders.instruction import Instruction
from solders.keypair import Keypair

from solana.spl.memo import MEMO_V4_PROGRAM_ID, MEMO_V3_PROGRAM_ID, AddMemoParams, add_memo, parse_add_memo


def test_add_memo_roundtrip():
    signer = Keypair().pubkey()
    ix = add_memo(AddMemoParams(memo="héllo", signers=(signer,)))
    assert ix.program_id == MEMO_V4_PROGRAM_ID
    assert ix.data == "héllo".encode()
    assert [(a.pubkey, a.is_signer, a.is_writable) for a in ix.accounts] == [(signer, True, False)]

    parsed = parse_add_memo(ix)
    assert (parsed.program_id, parsed.data.memo) == (MEMO_V4_PROGRAM_ID, "héllo")


def test_add_memo_without_signers_and_custom_program():
    ix = add_memo(AddMemoParams(memo="hi", program_id=MEMO_V3_PROGRAM_ID))
    assert ix.accounts == []
    assert parse_add_memo(ix).program_id == MEMO_V3_PROGRAM_ID


def test_parse_rejects_invalid_utf8():
    with pytest.raises(ValueError):
        parse_add_memo(Instruction(MEMO_V4_PROGRAM_ID, b"\xff\xfe", []))
