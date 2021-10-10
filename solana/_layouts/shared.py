"""Shared layouts."""
from construct import Bytes, Int32ul, Int64ul, PaddedString, Padding  # type: ignore
from construct import Struct as cStruct

FEE_CALCULATOR_LAYOUT = cStruct("lamports_per_signature" / Int64ul)

HASH_LAYOUT = Bytes(32)

PUBLIC_KEY_LAYOUT = Bytes(32)

RUST_STRING_LAYOUT = cStruct(
    "length" / Int32ul,
    Padding(4),
    "chars" / PaddedString(lambda this: this.length, "utf-8"),
)
