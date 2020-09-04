"""Shared layouts."""
from construct import Bytes, Int32ul, PaddedString, Padding  # type: ignore
from construct import Struct as cStruct

PUBLIC_KEY_LAYOUT = Bytes(32)

RUST_STRING_LAYOUT = cStruct(
    "length" / Int32ul,
    Padding(4),
    "chars" / PaddedString(lambda this: this.length, "utf-8"),
)
