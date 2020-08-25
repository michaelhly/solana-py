"""Integration test utils."""
import time

from solanarpc.api import Client
from solanarpc.rpc_types import RPCResponse


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
