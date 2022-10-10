"""Integration test utils."""
from typing import get_args

from solders.rpc.responses import RpcError, RpcResponseContext, RPCResult

from solana.rpc.commitment import Processed
from solana.rpc.types import RPCResponse, TxOpts

AIRDROP_AMOUNT = 10_000_000_000

RPC_RESULT_TYPES = get_args(RPCResult)


def assert_valid_response(resp: RPCResult):
    """Assert valid RPCResult."""
    assert type(resp) in RPC_RESULT_TYPES
    assert not isinstance(resp, RpcError)


def compare_responses_without_ids(left: RPCResponse, right: RPCResponse) -> None:
    """Compare RPC responses but ignore IDs."""
    assert {key: val for key, val in left.items() if key != "id"} == {
        key: val for key, val in right.items() if key != "id"
    }


OPTS = TxOpts(skip_confirmation=False, preflight_commitment=Processed)
