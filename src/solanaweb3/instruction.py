"""Library to encode/decode instruction data."""
from struct import unpack, Struct
from typing import Any, NamedTuple, Tuple


class InstructionLayout(NamedTuple):
    """Data layout for the instruction to be encoded.

    :param idx: The Instruction index (from solana upstream program)

    :param fmt: Format to build the instruction data

    Instruction formats follow the format conventions
    [here](https://docs.python.org/3/library/struct.html#format-strings).
    """

    idx: int
    fmt: str


def encode_data(layout: InstructionLayout, *params: Any) -> bytes:
    """Encode instruction data to raw bytes."""
    return Struct(layout.fmt).pack(layout.idx, *params)


def decode_data(layout: InstructionLayout, raw_data: bytes) -> Tuple:
    """Decode instruction from raw bytes."""
    data = None
    try:
        data = unpack(layout.fmt, raw_data)
    except Exception as err:
        raise RuntimeError("failed to decode instruction") from err
    if data[0] != layout.idx:
        raise ValueError(f"invalid instruction; instruction index mismatch {data[0]} != {layout.idx}")
    return data
