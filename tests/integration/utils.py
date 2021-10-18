"""Integration test utils."""

from solana.rpc.types import RPCResponse

AIRDROP_AMOUNT = 10_000_000_000


def assert_valid_response(resp: RPCResponse):
    """Assert valid RPCResponse."""
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"]
    assert resp["result"]


def compare_responses_without_ids(left: RPCResponse, right: RPCResponse) -> None:
    """Compare RPC responses but ignore IDs."""
    assert {key: val for key, val in left.items() if key != "id"} == {
        key: val for key, val in right.items() if key != "id"
    }
