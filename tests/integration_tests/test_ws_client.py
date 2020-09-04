"""Tests for the WS API Client."""
import pytest

from solana.publickey import PublicKey
from solana.rpc.websocket import WebSocketClient

from .utils import assert_valid_response

RETEST_LIMIT = 10
ENDPOINT = "ws://localhost:8900"


@pytest.mark.integration
@pytest.fixture(scope="session")
def test_ws_client(docker_services) -> WebSocketClient:
    """Test http_client.is_connected."""
    ws_client = WebSocketClient(ENDPOINT)
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
def test_slot_subscribe():  # pylint: disable=redefined-outer-name
    """Test slot subscribe."""
    ws_client_singleton = WebSocketClient(ENDPOINT)
    resp = ws_client_singleton.slot_subscribe()
    assert_valid_response(resp)


@pytest.mark.integration
def test_slot_unsubscribe():  # pylint: disable=redefined-outer-name
    """Test slot unsubscribe."""
    ws_client_singleton = WebSocketClient(ENDPOINT)
    sub_id = ws_client_singleton.slot_subscribe()["result"]
    resp = ws_client_singleton.slot_unsubscribe(sub_id)
    assert_valid_response(resp)


@pytest.mark.integration
def test_root_subscribe():  # pylint: disable=redefined-outer-name
    """Test root subscribe."""
    ws_client_singleton = WebSocketClient(ENDPOINT)
    resp = ws_client_singleton.root_subscribe()
    assert_valid_response(resp)


@pytest.mark.integration
def test_root_unsubscribe():  # pylint: disable=redefined-outer-name
    """Test root unsubscribe."""
    ws_client_singleton = WebSocketClient(ENDPOINT)
    sub_id = ws_client_singleton.root_subscribe()["result"]
    resp = ws_client_singleton.root_unsubscribe(sub_id)
    assert_valid_response(resp)


@pytest.mark.integration
def test_vote_subscribe():  # pylint: disable=redefined-outer-name
    """Test vote subscribe."""
    ws_client_singleton = WebSocketClient(ENDPOINT)
    resp = ws_client_singleton.vote_subscribe()
    assert_valid_response(resp)


@pytest.mark.integration
def test_vote_unsubscribe():  # pylint: disable=redefined-outer-name
    """Test vote unsubscribe."""
    ws_client_singleton = WebSocketClient(ENDPOINT)
    sub_id = ws_client_singleton.vote_subscribe()["result"]
    resp = ws_client_singleton.vote_unsubscribe(sub_id)
    assert_valid_response(resp)
