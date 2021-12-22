from unittest.mock import patch
from requests.exceptions import ReadTimeout

import pytest

from solana.exceptions import SolanaRpcException
from solana.publickey import PublicKey
from solana.rpc.commitment import Finalized


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


def test_client_address2_sig_args_no_commitmment(unit_test_http_client_async):
    expected = (
        "getConfirmedSignaturesForAddress2",
        "11111111111111111111111111111111",
        {"before": "before", "until": "until", "limit": 5},
    )
    actual = unit_test_http_client_async._get_confirmed_signature_for_address2_args(
        PublicKey(0), "before", "until", 5, None
    )
    assert expected == actual


def test_client_address_sig_args_no_commitment(unit_test_http_client_async):
    expected = (
        "getSignaturesForAddress",
        "11111111111111111111111111111111",
        {"before": "before", "until": "until", "limit": 5},
    )
    actual = unit_test_http_client_async._get_signatures_for_address_args(PublicKey(0), "before", "until", 5, None)
    assert expected == actual


def test_client_address2_sig_args_with_commitmment(unit_test_http_client_async):
    expected = (
        "getConfirmedSignaturesForAddress2",
        "11111111111111111111111111111111",
        {"limit": 5, "commitment": "finalized"},
    )
    actual = unit_test_http_client_async._get_confirmed_signature_for_address2_args(
        PublicKey(0), None, None, 5, Finalized
    )
    assert expected == actual


def test_client_address_sig_args_with_commitment(unit_test_http_client_async):
    expected = (
        "getSignaturesForAddress",
        "11111111111111111111111111111111",
        {"limit": 5, "commitment": "finalized"},
    )
    actual = unit_test_http_client_async._get_signatures_for_address_args(PublicKey(0), None, None, 5, Finalized)
    assert expected == actual
