"""Tools for getting RPC cluster information."""

from __future__ import annotations

from typing import Literal, NamedTuple
from typing_extensions import deprecated

from solana.rpc.models import ClusterUrls as ClusterUrlsModel, Endpoint as EndpointModel


@deprecated("ClusterUrls is deprecated; use solana.rpc.models instead.")
class ClusterUrls(NamedTuple):
    """A collection of urls for each cluster."""

    devnet: str
    testnet: str
    mainnet_beta: str


@deprecated("Endpoint is deprecated; use solana.rpc.models instead.")
class Endpoint(NamedTuple):
    """Container for http and https cluster urls."""

    http: ClusterUrls
    https: ClusterUrls


ENDPOINT = EndpointModel(
    http=ClusterUrlsModel(
        devnet="http://api.devnet.solana.com",
        testnet="http://api.testnet.solana.com",
        mainnet_beta="http://api.mainnet-beta.solana.com/",
    ),
    https=ClusterUrlsModel(
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
