"""Client for the Memo program."""

from solana.spl.memo.instructions import AddMemoParams, ParsedAddMemoInstruction, add_memo, parse_add_memo
from solana.spl.memo.programs import MEMO_PROGRAM_ID, MEMO_V1_PROGRAM_ID, MEMO_V3_PROGRAM_ID

__all__ = [
    "MEMO_PROGRAM_ID",
    "MEMO_V1_PROGRAM_ID",
    "MEMO_V3_PROGRAM_ID",
    "AddMemoParams",
    "ParsedAddMemoInstruction",
    "add_memo",
    "parse_add_memo",
]
