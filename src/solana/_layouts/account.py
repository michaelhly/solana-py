"""Byte layouts for account data."""
from enum import IntEnum

from construct import Int32ul, Pass, Switch  # type: ignore
from construct import Struct as cStruct

from .shared import FEE_CALCULATOR_LAYOUT, HASH_LAYOUT, PUBLIC_KEY_LAYOUT


class StateType(IntEnum):
    """State type for nonce accounts."""

    UNINITIALIZED = 0
    INITIALIZED = 1


class VersionsType(IntEnum):
    """Versions type for nonce accounts."""

    CURRENT = 0


_DATA_LAYOUT = cStruct(
    "authority" / PUBLIC_KEY_LAYOUT,
    "blockhash" / HASH_LAYOUT,
    "fee_calculator" / FEE_CALCULATOR_LAYOUT,
)


_STATE_LAYOUT = cStruct(
    "state_type" / Int32ul,
    "data"
    / Switch(
        lambda this: this.state_type,
        {
            StateType.UNINITIALIZED: Pass,
            StateType.INITIALIZED: _DATA_LAYOUT,
        },
    ),
)


VERSIONS_LAYOUT = cStruct(
    "versions_type" / Int32ul, "state" / Switch(lambda this: this.versions_type, {VersionsType.CURRENT: _STATE_LAYOUT})
)
