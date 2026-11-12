"""Tests for the new solana.spl.memo client."""

import pytest
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair

from solana.spl.memo import MEMO_PROGRAM_ID, MEMO_V3_PROGRAM_ID, AddMemoParams, add_memo, parse_add_memo


def test_add_memo_roundtrip():
    signer = Keypair().pubkey()
    ix = add_memo(AddMemoParams(memo="héllo", signers=(signer,)))
    assert ix.program_id == MEMO_PROGRAM_ID
    assert ix.data == "héllo".encode()
    assert [(a.pubkey, a.is_signer, a.is_writable) for a in ix.accounts] == [(signer, True, False)]

    parsed = parse_add_memo(ix)
    assert (parsed.program_id, parsed.signers, parsed.memo) == (MEMO_PROGRAM_ID, (signer,), "héllo")


def test_add_memo_without_signers_and_custom_program():
    ix = add_memo(AddMemoParams(memo="hi", program_id=MEMO_V3_PROGRAM_ID))
    assert ix.accounts == []
    assert parse_add_memo(ix).program_id == MEMO_V3_PROGRAM_ID


def test_parse_rejects_invalid_utf8():
    with pytest.raises(ValueError):
        parse_add_memo(Instruction(MEMO_PROGRAM_ID, b"\xff\xfe", []))


def test_parse_rejects_non_signer_account():
    meta = AccountMeta(Keypair().pubkey(), is_signer=False, is_writable=False)
    with pytest.raises(ValueError):
        parse_add_memo(Instruction(MEMO_PROGRAM_ID, b"hi", [meta]))
