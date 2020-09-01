"""Tests for the WS API Client."""
import pytest

from solana.publickey import PublicKey
from solana.rpc.websocket import WebSocketClient

from .utils import assert_valid_response

RETEST_LIMIT = 10

ID = {}


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_ws_client(docker_services) -> WebSocketClient:
    """Test http_client.is_connected."""
    ws_client = WebSocketClient("ws://localhost:8900")
    docker_services.wait_until_responsive(timeout=15, pause=1, check=ws_client.is_connected)
    return ws_client


@pytest.mark.integration
def test_account_subscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test account subscription."""
    resp = test_ws_client.account_subscribe(PublicKey(1))
    assert_valid_response(resp)


@pytest.mark.integration
def test_account_unsubscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test account unsubscription."""
    sub_id = test_ws_client.account_subscribe(PublicKey(1))["result"]
    resp = test_ws_client.account_unsubscribe(sub_id)
    assert_valid_response(resp)


@pytest.mark.integration
def test_program_subscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test program subscription."""
    resp = test_ws_client.program_subscribe(PublicKey(1))
    assert_valid_response(resp)


@pytest.mark.integration
def test_program_unsubscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test program unsubscribe."""
    sub_id = test_ws_client.program_subscribe(PublicKey(1))["result"]
    resp = test_ws_client.program_unsubscribe(sub_id)
    assert_valid_response(resp)


@pytest.mark.integration
def test_signature_subscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test signature subscribe."""
    resp = test_ws_client.signature_subscribe(
        "2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b"
    )
    assert_valid_response(resp)


@pytest.mark.integration
def test_signature_unsubscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test signature unsubscribe."""
    sub_id = test_ws_client.signature_subscribe(
        "2EBVM6cB8vAAD93Ktr6Vd8p67XPbQzCJX47MpReuiCXJAtcjaxpvWpcg9Ege1Nr5Tk3a2GFrByT7WPBjdsTycY9b"
    )["result"]
    resp = test_ws_client.signature_unsubscribe(sub_id)
    assert_valid_response(resp)


@pytest.mark.integration
def test_slot_subscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test slot subscribe."""
    resp = test_ws_client.slot_subscribe()
    if "result" in resp:
        assert_valid_response(resp)
        ID["slot"] = resp["result"]
    else:
        assert resp["jsonrpc"] == "2.0"
        assert resp["params"]
        assert resp["method"]


@pytest.mark.integration
def test_slot_unsubscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test slot unsubscribe."""
    sub_id = ID.get("slot", test_ws_client.slot_subscribe()["result"])
    resp = test_ws_client.slot_unsubscribe(sub_id)
    if "result" in resp:
        assert_valid_response(resp)
    else:
        assert resp["jsonrpc"] == "2.0"
        assert resp["params"]
        assert resp["method"]
    if "slot" in ID:
        ID.pop("slot")


@pytest.mark.integration
def test_root_subscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test root subscribe."""
    resp = test_ws_client.root_subscribe()
    assert_valid_response(resp)
    ID["root"] = resp["result"]


@pytest.mark.integration
def test_root_unsubscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test root unsubscribe."""
    sub_id = ID.get("root", test_ws_client.root_subscribe()["result"])
    resp = test_ws_client.root_unsubscribe(sub_id)
    assert_valid_response(resp)
    if "root" in ID:
        ID.pop("root")


@pytest.mark.integration
def test_vote_subscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test vote subscribe."""
    resp = test_ws_client.vote_subscribe()
    assert_valid_response(resp)
    ID["vote"] = resp["result"]


@pytest.mark.integration
def test_vote_unsubscribe(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test vote unsubscribe."""
    sub_id = ID.get("vote", test_ws_client.vote_subscribe()["result"])
    resp = test_ws_client.vote_unsubscribe(sub_id)
    assert_valid_response(resp)
    if "vote" in ID:
        ID.pop("vote")


@pytest.mark.integration
def test_is_connected(test_ws_client):  # pylint: disable=redefined-outer-name
    """Test connection."""
    resp = test_ws_client.is_connected()
    assert resp
