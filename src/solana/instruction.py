"""Library to encode/decode instruction data."""
from struct import Struct, unpack
from typing import Any, NamedTuple, Tuple


class InstructionLayout(NamedTuple):
    """Data layout for the instruction to be encoded.

    Instruction formats follow the format conventions `here
    <https://docs.python.org/3/library/struct.html#struct-format-strings/>`_.
    """

    idx: int
    """The Instruction index (from solana upstream program)."""
    fmt: str
    """Format to build the parameter data."""


def encode_data(layout: InstructionLayout, *params: Any) -> bytes:
    """Encode instruction data to raw bytes.

    >>> # Encoding a transfer instruction:
    >>> transfer_layout = InstructionLayout(idx=2, fmt="Q")
    >>> encode_data(transfer_layout, 123).hex()
    '020000007b00000000000000'
    """
    return Struct(f"<I{layout.fmt}").pack(layout.idx, *params)


def decode_data(layout: InstructionLayout, raw_data: bytes) -> Tuple:
    """Decode instruction from raw bytes.

    >>> # Decoding a transfer instruction:
    >>> transfer_layout = InstructionLayout(idx=2, fmt="Q")
    >>> raw_data = bytes.fromhex('020000007b00000000000000')
    >>> decode_data(transfer_layout, raw_data)
    (2, 123)
    """
    data = None
    try:
        data = unpack(f"<I{layout.fmt}", raw_data)
    except Exception as err:
        raise RuntimeError("failed to decode instruction") from err
    if data[0] != layout.idx:
        raise ValueError(f"invalid instruction; instruction index mismatch {data[0]} != {layout.idx}")
    return data
