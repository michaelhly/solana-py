"""Tools for getting RPC cluster information."""

from __future__ import annotations

from typing import Literal, NamedTuple
from typing_extensions import deprecated


@deprecated("ClusterUrls is deprecated and will be replaced by a Pydantic model.")
class ClusterUrls(NamedTuple):
    """A collection of urls for each cluster."""

    devnet: str
    testnet: str
    mainnet_beta: str


@deprecated("Endpoint is deprecated and will be replaced by a Pydantic model.")
class Endpoint(NamedTuple):
    """Container for http and https cluster urls."""

    http: ClusterUrls
    https: ClusterUrls


ENDPOINT = Endpoint(
    http=ClusterUrls(
        devnet="http://api.devnet.solana.com",
        testnet="http://api.testnet.solana.com",
        mainnet_beta="http://api.mainnet-beta.solana.com/",
    ),
    https=ClusterUrls(
        devnet="https://api.devnet.solana.com",
        testnet="https://api.testnet.solana.com",
        mainnet_beta="https://api.mainnet-beta.solana.com/",
    ),
)


Cluster = Literal["devnet", "testnet", "mainnet-beta"]


def cluster_api_url(cluster: Cluster | None = None, tls: bool = True) -> str:
    """Retrieve the RPC API URL for the specified cluster.

    :param cluster: The name of the cluster to use.
    :param tls: If True, use https. Defaults to True.
    """
    urls = ENDPOINT.https if tls else ENDPOINT.http
    if cluster is None:
        return urls.devnet
    return getattr(urls, cluster)
