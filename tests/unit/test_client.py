from unittest.mock import patch
from requests.exceptions import ReadTimeout
import pytest

from solana.exceptions import SolanaRpcException


def test_client_http_exception(unit_test_http_client):
    """Test AsyncClient raises native Solana-py exceptions."""

    with patch("requests.post") as post_mock:
        post_mock.side_effect = ReadTimeout()
        with pytest.raises(SolanaRpcException) as exc_info:
            unit_test_http_client.get_epoch_info()
        assert exc_info.type == SolanaRpcException
        assert (
            exc_info.value.error_msg
            == "<class 'requests.exceptions.ReadTimeout'> raised in \"getEpochInfo\" endpoint request"
        )
