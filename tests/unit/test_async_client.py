"""Test async client."""

from unittest.mock import patch

import pytest
from httpx2 import ReadTimeout
from solders.account_decoder import UiAccountEncoding, UiDataSliceConfig
from solders.commitment_config import CommitmentLevel
from solders.pubkey import Pubkey
from solders.rpc.config import (
    RpcAccountInfoConfig,
    RpcProgramAccountsConfig,
    RpcSignaturesForAddressConfig,
    RpcTokenAccountsFilterProgramId,
)
from solders.rpc.filter import Memcmp
from solders.rpc.requests import (
    GetAccountInfo,
    GetMultipleAccounts,
    GetProgramAccounts,
    GetSignaturesForAddress,
    GetTokenAccountsByOwner,
)
from solders.signature import Signature

from solana.constants import SYSTEM_PROGRAM_ID
from solana.exceptions import SolanaRpcException
from solana.rpc.commitment import Finalized
from solana.rpc.models import DataSliceOpts, MemcmpOpts, TokenAccountOpts


async def test_async_client_http_exception(unit_test_http_client_async):
    """Test AsyncClient raises native Solana-py exceptions."""
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.side_effect = ReadTimeout("placeholder")
        with pytest.raises(SolanaRpcException) as exc_info:
            await unit_test_http_client_async.get_epoch_info()
        assert exc_info.type == SolanaRpcException
        assert exc_info.value.error_msg == "<class 'httpx2.ReadTimeout'> raised in \"GetEpochInfo\" endpoint request"


def test_client_address_sig_args_no_commitment(unit_test_http_client_async):
    """Test generating getSignaturesForAddressBody."""
    expected = GetSignaturesForAddress(
        SYSTEM_PROGRAM_ID,
        RpcSignaturesForAddressConfig(
            limit=5,
            before=Signature.default(),
            until=Signature.default(),
            commitment=CommitmentLevel.Processed,
        ),
    )
    actual = unit_test_http_client_async._get_signatures_for_address_body(
        Pubkey([0] * 31 + [0]),
        before=Signature.default(),
        until=Signature.default(),
        limit=5,
        commitment=None,
    )
    assert expected == actual


def test_client_address_sig_args_with_commitment(unit_test_http_client_async):
    expected = GetSignaturesForAddress(
        SYSTEM_PROGRAM_ID,
        RpcSignaturesForAddressConfig(limit=5, commitment=CommitmentLevel.Finalized),
    )
    actual = unit_test_http_client_async._get_signatures_for_address_body(
        Pubkey([0] * 31 + [0]), None, None, 5, Finalized
    )
    assert expected == actual


def test_get_account_info_body(unit_test_http_client_async):
    """Test generating getAccountInfo body with a data slice."""
    pubkey = Pubkey([0] * 31 + [0])
    expected = GetAccountInfo(
        pubkey,
        RpcAccountInfoConfig(
            encoding=UiAccountEncoding.Base64,
            data_slice=UiDataSliceConfig(offset=1, length=2),
            commitment=CommitmentLevel.Processed,
        ),
    )
    actual = unit_test_http_client_async._get_account_info_body(
        pubkey=pubkey, commitment=None, encoding="base64", data_slice=DataSliceOpts(offset=1, length=2)
    )
    assert expected == actual


def test_get_multiple_accounts_body(unit_test_http_client_async):
    """Test generating getMultipleAccounts body with a data slice."""
    pubkeys = [Pubkey([0] * 31 + [0])]
    expected = GetMultipleAccounts(
        pubkeys,
        RpcAccountInfoConfig(
            encoding=UiAccountEncoding.Base64,
            commitment=CommitmentLevel.Processed,
            data_slice=UiDataSliceConfig(offset=1, length=2),
        ),
    )
    actual = unit_test_http_client_async._get_multiple_accounts_body(
        pubkeys=pubkeys, commitment=None, encoding="base64", data_slice=DataSliceOpts(offset=1, length=2)
    )
    assert expected == actual


def test_get_program_accounts_body(unit_test_http_client_async):
    """Test generating getProgramAccounts body with a data slice and memcmp filters."""
    pubkey = Pubkey([0] * 31 + [0])
    expected = GetProgramAccounts(
        pubkey,
        RpcProgramAccountsConfig(
            RpcAccountInfoConfig(
                encoding=UiAccountEncoding.Base64,
                commitment=CommitmentLevel.Processed,
                data_slice=UiDataSliceConfig(offset=1, length=2),
            ),
            [17, Memcmp(offset=4, bytes_="3Mc6vR")],
        ),
    )
    actual = unit_test_http_client_async._get_program_accounts_body(
        pubkey=pubkey,
        commitment=None,
        encoding="base64",
        data_slice=DataSliceOpts(offset=1, length=2),
        filters=[17, MemcmpOpts(offset=4, bytes="3Mc6vR")],
    )
    assert expected == actual


def test_get_token_accounts_by_owner_body(unit_test_http_client_async):
    """Test generating getTokenAccountsByOwner body from token account opts."""
    owner = Pubkey([0] * 31 + [0])
    expected = GetTokenAccountsByOwner(
        owner,
        RpcTokenAccountsFilterProgramId(SYSTEM_PROGRAM_ID),
        RpcAccountInfoConfig(
            encoding=UiAccountEncoding.Base64,
            commitment=CommitmentLevel.Processed,
            data_slice=None,
        ),
    )
    actual = unit_test_http_client_async._get_token_accounts_by_owner_body(
        owner, TokenAccountOpts(program_id=SYSTEM_PROGRAM_ID), None
    )
    assert expected == actual
