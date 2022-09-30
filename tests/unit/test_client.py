from unittest.mock import patch

import pytest
from solders.rpc.requests import GetSignaturesForAddress
from solders.rpc.config import RpcSignaturesForAddressConfig
from solders.commitment_config import CommitmentLevel
from solders.pubkey import Pubkey
from solders.signature import Signature
from requests.exceptions import ReadTimeout

from solana.exceptions import SolanaRpcException
from solana.publickey import PublicKey
from solana.rpc.commitment import Finalized


def test_client_http_exception(unit_test_http_client):
    """Test AsyncClient raises native Solana-py exceptions."""

    with patch("requests.post") as post_mock:
        post_mock.side_effect = ReadTimeout()
        with pytest.raises(SolanaRpcException) as exc_info:
            unit_test_http_client.get_epoch_info()
        assert exc_info.type == SolanaRpcException
        assert (
            exc_info.value.error_msg
            == "<class 'requests.exceptions.ReadTimeout'> raised in \"GetEpochInfo\" endpoint request"
        )


def test_client_address_sig_args_no_commitment(unit_test_http_client):
    expected = GetSignaturesForAddress(
        Pubkey.from_string("11111111111111111111111111111111"),
        RpcSignaturesForAddressConfig(
            limit=5, before=Signature.default(), until=Signature.default(), commitment=CommitmentLevel.Processed
        ),
    )
    actual = unit_test_http_client._get_signatures_for_address_body(
        PublicKey(0), before=Signature.default(), until=Signature.default(), limit=5, commitment=None
    )
    assert expected == actual


def test_client_address_sig_args_with_commitment(unit_test_http_client):
    expected = GetSignaturesForAddress(
        Pubkey.from_string("11111111111111111111111111111111"),
        RpcSignaturesForAddressConfig(limit=5, commitment=CommitmentLevel.Finalized),
    )
    actual = unit_test_http_client._get_signatures_for_address_body(PublicKey(0), None, None, 5, Finalized)
    assert expected == actual
