"""Integration test utils."""
import time

from typing import Callable, Optional, Union
from inspect import getfullargspec

from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import RPCResponse
from solana.rpc.websocket import WebSocketClient


def assert_valid_response(resp: RPCResponse):
    """Assert valid RPCResponse."""
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"]
    assert resp["result"]


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


def get_subscription_id(
    client: WebSocketClient, subscription_method: Callable[[Optional[Union[PublicKey, str]]], int]
) -> int:
    """Gets a subscription id for unsubscription testing"""
    i = 0
    RETEST_LIMIT = 10  # 10 times pylint: disable=invalid-name
    subscription_response = None
    if len(getfullargspec(subscription_method)[0]) == 0:
        subscription_response = client.subscription_method()
    else:
        subscription_response = client.subscription_method(PublicKey(1))
    while "result" not in subscription_response and i < RETEST_LIMIT:
        i += 1
        time.sleep(i)
        subscription_response = client.subscription_method(PublicKey(1))
    if "result" not in subscription_response:
        raise RuntimeError("could not subscribe: ", subscription_method)
    return subscription_response["result"]
