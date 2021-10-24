"""Library for ShortVec encoding."""
from typing import Tuple


def decode_length(raw_bytes: bytes) -> Tuple[int, int]:
    """Return the decoded length and how many bytes it consumed."""
    length = size = 0
    while size < len(raw_bytes):
        elem = raw_bytes[size]
        length |= (elem & 0x7F) << (size * 7)
        size += 1
        if (elem & 0x80) == 0:
            break
    return length, size


def encode_length(value: int) -> bytes:
    """Return the serialized length in compact-u16 format."""
    elems, rem_len = [], value
    while True:
        elem = rem_len & 0x7F
        rem_len >>= 7
        if not rem_len:
            elems.append(elem)
            break
        elem |= 0x80
        elems.append(elem)
    return bytes(elems)
