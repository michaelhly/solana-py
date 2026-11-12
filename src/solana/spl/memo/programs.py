"""Memo program addresses."""

from solders.pubkey import Pubkey

MEMO_V4_PROGRAM_ID: Pubkey = Pubkey.from_string("Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH")
"""Current (v4) Memo program."""

MEMO_V3_PROGRAM_ID: Pubkey = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
"""Legacy v3 program, wire-compatible with v4. Kept for historical transactions."""

MEMO_V1_PROGRAM_ID: Pubkey = Pubkey.from_string("Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo")
"""Legacy v1 program. Kept for historical transactions."""
