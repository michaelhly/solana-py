from unittest.mock import patch
from requests.exceptions import ReadTimeout

import pytest

from solana.exceptions import SolanaRpcException


@pytest.mark.asyncio
async def test_async_client_http_exception(unit_test_http_client_async):
    """Test AsyncClient raises native Solana-py exceptions."""

    with patch("httpx.AsyncClient.post") as post_mock:
        post_mock.side_effect = ReadTimeout()
        with pytest.raises(SolanaRpcException) as exc_info:
            await unit_test_http_client_async.get_epoch_info()
        assert exc_info.type == SolanaRpcException
        assert (
            exc_info.value.error_msg
            == "<class 'requests.exceptions.ReadTimeout'> raised in \"getEpochInfo\" endpoint request"
        )
