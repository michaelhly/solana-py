"""Test async client."""

import json
from inspect import signature
from unittest.mock import patch

from httpx2 import ReadError, ReadTimeout
import httpx2
import pytest
from pydantic import BaseModel, ValidationError
from solders.account_decoder import UiAccountEncoding, UiDataSliceConfig
from solders.commitment_config import CommitmentLevel
from solders.pubkey import Pubkey
from solders.rpc.config import (
    RpcAccountInfoConfig,
    RpcBlockConfig,
    RpcProgramAccountsConfig,
    RpcSignaturesForAddressConfig,
    RpcTokenAccountsFilterProgramId,
)
from solders.rpc.filter import Memcmp
from solders.rpc.requests import (
    GetAccountInfo,
    GetBlock,
    GetMultipleAccounts,
    GetProgramAccounts,
    GetSignaturesForAddress,
    GetTokenAccountsByOwner,
)
from solders.signature import Signature
from solders.transaction_status import TransactionDetails, UiTransactionEncoding

from solana.constants import SYSTEM_PROGRAM_ID
from solana._pydantic import PydanticModel
from solana.exceptions import SolanaRpcException
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Finalized
from solana.rpc.async_http_provider import AsyncHTTPProvider
from solana.rpc.jsonrpc import JsonRpcErrorObject, JsonRpcRequest, SolanaJsonRpcError
from solana.rpc.models import DataSliceOpts, MemcmpOpts, TokenAccountOpts


class _TestRpcRequest(JsonRpcRequest):
    """Test JSON-RPC request."""

    method: str = "testMethod"


class _TypedRpcParams(PydanticModel):
    """Test typed JSON-RPC params."""

    value: int


class _TypedRpcRequest(JsonRpcRequest):
    """Test JSON-RPC request with typed params."""

    method: str = "typedMethod"
    params: list[_TypedRpcParams] | None = None


class _LooseRpcRequest(BaseModel):
    """Test request that does not inherit the JSON-RPC request base."""

    method: str = "testMethod"

    def to_json(self) -> str:
        """Serialize the request to JSON."""
        return self.model_dump_json(exclude_none=True)


class _TestRpcResult(PydanticModel):
    """Test JSON-RPC result."""

    value: int


class _CustomRpcError(SolanaJsonRpcError):
    """Test custom JSON-RPC error."""

    def __init__(self, code: int, message: str, request_id: str | int, method: str | None) -> None:
        """Initialize test custom JSON-RPC error."""
        super().__init__(code, message, request_id=request_id, method=method)


def _mock_response(text: str) -> httpx2.Response:
    return httpx2.Response(200, text=text, request=httpx2.Request("POST", "http://localhost:8899"))


def test_jsonrpc_request_to_json_forwards_model_dump_json_kwargs():
    model_dump_json_parameters = list(signature(BaseModel.model_dump_json).parameters)
    to_json_parameters = list(signature(JsonRpcRequest.to_json).parameters)
    assert to_json_parameters == model_dump_json_parameters

    dumped = _TestRpcRequest().to_json(exclude_none=False, indent=2)
    assert "\n" in dumped
    assert json.loads(dumped) == {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "testMethod",
        "params": None,
    }


def test_jsonrpc_request_params_are_untyped_by_default():
    request = JsonRpcRequest.model_validate({"method": "testMethod", "params": {"value": 2}})

    assert request.params == {"value": 2}
    assert json.loads(request.to_json()) == {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "testMethod",
        "params": {"value": 2},
    }


def test_jsonrpc_request_subclasses_can_override_params():
    request = _TypedRpcRequest.model_validate({"params": [{"value": 2}]})

    assert request.params == [_TypedRpcParams(value=2)]
    assert json.loads(request.to_json()) == {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "typedMethod",
        "params": [{"value": 2}],
    }


def test_jsonrpc_request_typed_params_must_be_list():
    with pytest.raises(ValidationError):
        _TypedRpcRequest.model_validate({"params": {"value": 2}})


def test_solana_jsonrpc_error_to_json():
    error = SolanaJsonRpcError.from_error_object(
        JsonRpcErrorObject(code=-32602, message="Invalid params"),
        request_id="1",
        method="testMethod",
    )

    assert json.loads(error.to_json()) == {
        "code": -32602,
        "message": "Invalid params",
        "data": None,
        "request_id": "1",
        "method": "testMethod",
        "name": "INVALID_PARAMS",
    }
    assert json.loads(error.to_json(exclude_none=True)) == {
        "code": -32602,
        "message": "Invalid params",
        "request_id": "1",
        "method": "testMethod",
        "name": "INVALID_PARAMS",
    }


def test_async_http_provider_uses_httpx2_defaults():
    """Test AsyncHTTPProvider leaves timeout and limits at httpx2 defaults."""
    with patch("httpx2.AsyncClient") as client_mock:
        AsyncHTTPProvider()
    client_mock.assert_called_once_with(http2=True)


def test_async_http_provider_passes_explicit_http_options():
    """Test AsyncHTTPProvider passes explicit transport configuration."""
    with patch("httpx2.AsyncClient") as client_mock:
        AsyncHTTPProvider(
            timeout=3.0,
            proxy="http://localhost:8899",
            max_connections=8,
            max_keepalive_connections=4,
            keepalive_expiry=2.0,
            http2=False,
        )
    client_mock.assert_called_once_with(
        http2=False,
        timeout=httpx2.Timeout(3.0),
        proxy="http://localhost:8899",
        limits=httpx2.Limits(
            max_connections=8,
            max_keepalive_connections=4,
            keepalive_expiry=2.0,
        ),
    )


def test_async_client_passes_explicit_http_options():
    """Test AsyncClient forwards explicit HTTP options to the provider."""
    with patch("solana.rpc.async_http_provider.AsyncHTTPProvider") as provider_mock:
        AsyncClient(
            timeout=3.0,
            max_connections=8,
            max_keepalive_connections=4,
            keepalive_expiry=2.0,
            http2=False,
            max_transport_retries=2,
        )
    provider_mock.assert_called_once_with(
        None,
        timeout=3.0,
        extra_headers=None,
        proxy=None,
        rate_limit=0,
        max_connections=8,
        max_keepalive_connections=4,
        keepalive_expiry=2.0,
        http2=False,
        max_transport_retries=2,
    )


async def test_async_client_http_exception(unit_test_http_client_async):
    """Test AsyncClient raises native Solana-py exceptions."""
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.side_effect = ReadTimeout("placeholder")
        with pytest.raises(SolanaRpcException) as exc_info:
            await unit_test_http_client_async.get_epoch_info()
        assert exc_info.type == SolanaRpcException
        assert exc_info.value.error_msg == "<class 'httpx2.ReadTimeout'> raised in \"GetEpochInfo\" endpoint request"


async def test_async_http_provider_retries_transport_error_once(
    unit_test_http_client_async,
):
    """Test AsyncHTTPProvider retries transient transport errors once."""
    raw = '{"jsonrpc":"2.0","id":1,"result":{"value":42}}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.side_effect = [ReadError("placeholder"), _mock_response(raw)]
        result = await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), _TestRpcResult)
    assert result == _TestRpcResult(value=42)
    assert post_mock.call_count == 2


async def test_async_http_provider_does_not_retry_http_status_error(
    unit_test_http_client_async,
):
    """Test AsyncHTTPProvider only retries transport errors."""
    response = httpx2.Response(
        500,
        text="server error",
        request=httpx2.Request("POST", "http://localhost:8899"),
    )
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = response
        with pytest.raises(SolanaRpcException) as exc_info:
            await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), _TestRpcResult)
    assert post_mock.call_count == 1
    assert exc_info.value.error_msg == "<class 'httpx2.HTTPStatusError'> raised in \"_TestRpcRequest\" endpoint request"


async def test_async_http_provider_can_disable_transport_retries():
    """Test max_transport_retries=0 disables transport retries."""
    provider = AsyncHTTPProvider(max_transport_retries=0)
    try:
        with patch("httpx2.AsyncClient.post") as post_mock:
            post_mock.side_effect = ReadError("placeholder")
            with pytest.raises(SolanaRpcException):
                await provider.make_request_unparsed(_TestRpcRequest())
        assert post_mock.call_count == 1
    finally:
        await provider.close()


async def test_send_rpc_request_success(unit_test_http_client_async):
    """Test sending a Pydantic-owned JSON-RPC request."""
    raw = '{"jsonrpc":"2.0","id":1,"result":{"value":42}}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = _mock_response(raw)
        result = await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), _TestRpcResult)
    assert result == _TestRpcResult(value=42)
    assert post_mock.call_args.kwargs["content"] == '{"jsonrpc":"2.0","id":"1","method":"testMethod"}'


async def test_send_rpc_request_requires_jsonrpc_request(unit_test_http_client_async):
    """Test send_rpc_request rejects loose serializers."""
    with pytest.raises(TypeError, match="request must be an instance of JsonRpcRequest"):
        await unit_test_http_client_async.send_rpc_request(_LooseRpcRequest(), _TestRpcResult)  # type: ignore[arg-type]


async def test_send_rpc_request_scalar_result(unit_test_http_client_async):
    """Test sending a JSON-RPC request with a scalar result type."""
    raw = '{"jsonrpc":"2.0","id":1,"result":42}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = _mock_response(raw)
        result = await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), int)
    assert result == 42


async def test_send_rpc_request_string_result(unit_test_http_client_async):
    """Test sending a JSON-RPC request with a string result type."""
    raw = '{"jsonrpc":"2.0","id":1,"result":"testLeader"}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = _mock_response(raw)
        result = await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), str)
    assert result == "testLeader"


async def test_send_rpc_request_object_result(unit_test_http_client_async):
    """Test sending a JSON-RPC request with an object result type."""
    raw = '{"jsonrpc":"2.0","id":1,"result":{"value":42}}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = _mock_response(raw)
        result = await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), dict[str, int])
    assert result == {"value": 42}


async def test_send_rpc_request_jsonrpc_error(unit_test_http_client_async):
    """Test JSON-RPC error responses are raised before result parsing."""
    raw = '{"jsonrpc":"2.0","id":"1","error":{"code":-32602,"message":"Invalid params"}}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = _mock_response(raw)
        with pytest.raises(SolanaJsonRpcError) as exc_info:
            await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), _TestRpcResult)
    assert exc_info.value.code == -32602
    assert exc_info.value.message == "Invalid params"
    assert exc_info.value.data is None
    assert exc_info.value.request_id == "1"
    assert exc_info.value.method == "testMethod"
    assert exc_info.value.name == "INVALID_PARAMS"


async def test_send_rpc_request_custom_error_parser(unit_test_http_client_async):
    """Test send_rpc_request accepts a custom JSON-RPC error parser."""

    def parse_error(
        error: JsonRpcErrorObject,
        *,
        request_id: str | int,
        method: str | None = None,
    ) -> Exception:
        return _CustomRpcError(error.code, error.message, request_id, method)

    raw = '{"jsonrpc":"2.0","id":7,"error":{"code":-32603,"message":"Provider-specific failure"}}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = _mock_response(raw)
        with pytest.raises(_CustomRpcError) as exc_info:
            await unit_test_http_client_async.send_rpc_request(
                _TestRpcRequest(id=7),
                _TestRpcResult,
                error_parser=parse_error,
            )
    assert exc_info.value.code == -32603
    assert exc_info.value.message == "Provider-specific failure"
    assert exc_info.value.request_id == 7
    assert exc_info.value.method == "testMethod"
    assert json.loads(exc_info.value.to_json(exclude_none=True)) == {
        "code": -32603,
        "message": "Provider-specific failure",
        "request_id": 7,
        "method": "testMethod",
    }


async def test_send_rpc_request_malformed_envelope(unit_test_http_client_async):
    """Test malformed JSON-RPC envelopes fail validation."""
    raw = '{"jsonrpc":"2.0","id":1}'
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.return_value = _mock_response(raw)
        with pytest.raises(ValidationError):
            await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), _TestRpcResult)


async def test_send_rpc_request_http_exception(unit_test_http_client_async):
    """Test send_rpc_request raises native Solana-py transport exceptions."""
    with patch("httpx2.AsyncClient.post") as post_mock:
        post_mock.side_effect = ReadTimeout("placeholder")
        with pytest.raises(SolanaRpcException) as exc_info:
            await unit_test_http_client_async.send_rpc_request(_TestRpcRequest(), _TestRpcResult)
    assert exc_info.value.error_msg == "<class 'httpx2.ReadTimeout'> raised in \"_TestRpcRequest\" endpoint request"


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
        pubkey=pubkey,
        commitment=None,
        encoding="base64",
        data_slice=DataSliceOpts(offset=1, length=2),
    )
    assert expected == actual


def test_get_block_body(unit_test_http_client_async):
    """Test generating getBlock body with full block config."""
    expected = GetBlock(
        2,
        RpcBlockConfig(
            encoding=UiTransactionEncoding.Json,
            transaction_details=TransactionDetails.Signatures,
            rewards=False,
            commitment=CommitmentLevel.Finalized,
            max_supported_transaction_version=0,
        ),
    )
    actual = unit_test_http_client_async._get_block_body(
        slot=2,
        encoding="json",
        max_supported_transaction_version=0,
        transaction_details=TransactionDetails.Signatures,
        rewards=False,
        commitment=Finalized,
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
        pubkeys=pubkeys,
        commitment=None,
        encoding="base64",
        data_slice=DataSliceOpts(offset=1, length=2),
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
