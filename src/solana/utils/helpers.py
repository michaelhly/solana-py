"""Helper functions."""

from base64 import b64decode
from typing import Dict, Union

from based58 import b58decode


def from_uint8_bytes(uint8: bytes) -> int:
    """Convert from uint8 to python int."""
    return int.from_bytes(uint8, byteorder="little")


def to_uint8_bytes(val: int) -> bytes:
    """Convert an integer to uint8."""
    return val.to_bytes(1, byteorder="little")


def decode_byte_string(byte_string: str, encoding: str = "base64") -> bytes:
    """Decode an encoded string from an RPC Response."""
    b_str = str.encode(byte_string)
    if encoding == "base64":
        return b64decode(b_str)
    if encoding == "base58":
        return b58decode(b_str)

    raise NotImplementedError(f"{encoding} decoding not currently supported.")


def merge_keep_latter(dict_1: Dict[str, Union[str, Dict]], dict_2: Dict[str, Union[str, Dict]]):
    """Deep-merges 2 dicts, preferring values from latter on conflict"""
    res = dict_1.copy()
    for (key, val) in dict_2.items():
        if isinstance(val, dict):
            if isinstance(res[key], dict):
                res[key] = merge_keep_latter(res[key], val)
            else:
                res[key] = val
        else:
            res[key] = val
    return res
