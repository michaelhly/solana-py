"""Integration test utils."""
import time
import asyncio
from base64 import b64decode

from base58 import b58decode

from solana.rpc.api import Client, AsyncClient
from solana.rpc.types import RPCResponse


def assert_valid_response(resp: RPCResponse):
    """Assert valid RPCResponse."""
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"]
    assert resp["result"]


def compare_responses_without_ids(left: RPCResponse, right: RPCResponse) -> None:
    """Compare RPC responses but ignore IDs"""
    assert {key: val for key, val in left.items() if key != "id"} == {
        key: val for key, val in right.items() if key != "id"
    }


def confirm_transaction(client: Client, tx_sig: str) -> RPCResponse:
    """Confirm a transaction."""
    TIMEOUT = 30  # 30 seconds  pylint: disable=invalid-name
    elapsed_time = 0
    while elapsed_time < TIMEOUT:
        sleep_time = 3
        if not elapsed_time:
            sleep_time = 7
            time.sleep(sleep_time)
        else:
            time.sleep(sleep_time)

        resp = client.get_confirmed_transaction(tx_sig)
        if resp["result"]:
            break
        elapsed_time += sleep_time

    if not resp["result"]:
        raise RuntimeError("could not confirm transaction: ", tx_sig)
    return resp


async def aconfirm_transaction(client: AsyncClient, tx_sig: str) -> RPCResponse:
    """Confirm a transaction."""
    TIMEOUT = 30  # 30 seconds  pylint: disable=invalid-name
    elapsed_time = 0
    while elapsed_time < TIMEOUT:
        sleep_time = 3
        if not elapsed_time:
            sleep_time = 7
            await asyncio.sleep(sleep_time)
        else:
            await asyncio.sleep(sleep_time)

        resp = await client.get_confirmed_transaction(tx_sig)
        if resp["result"]:
            break
        elapsed_time += sleep_time

    if not resp["result"]:
        raise RuntimeError("could not confirm transaction: ", tx_sig)
    return resp


def decode_byte_string(byte_string: str, encoding: str = "base64") -> bytes:
    """Decode a encoded string from an RPC Response."""
    b_str = str.encode(byte_string)
    if encoding == "base64":
        return b64decode(b_str)
    if encoding == "base58":
        return b58decode(b_str)

    raise NotImplementedError(f"{encoding} decoding not currently supported.")
