"""Shared layouts."""
from construct import Bytes, Int32ul, PaddedString, Padding
from construct import Struct as cStruct

PUBLIC_KEY_LAYOUT = Bytes(16)

RUST_STRING_LAYOUT = cStruct(
    "length" / Int32ul,
    Padding(4),
    "chars" / PaddedString(this.length, "utf-8"),
)
