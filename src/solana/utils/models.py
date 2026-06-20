"""Pydantic models for cluster utilities.

These are the Pydantic successors to the deprecated ``NamedTuple`` types in
:mod:`solana.utils.cluster`.
"""

from __future__ import annotations

from solana._pydantic import PydanticModel


class ClusterUrls(PydanticModel):
    """A collection of urls for each cluster."""

    devnet: str
    testnet: str
    mainnet_beta: str


class Endpoint(PydanticModel):
    """Container for http and https cluster urls."""

    http: ClusterUrls
    https: ClusterUrls
