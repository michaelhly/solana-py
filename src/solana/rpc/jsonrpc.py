"""JSON-RPC request and response helpers."""

from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from typing import Any, Literal, Protocol, TypeVar

from pydantic import BaseModel, model_validator
from pydantic.main import IncEx

from solana._pydantic import PydanticModel

JsonRpcId = int | str | None
JsonRpcParams = list[Any] | dict[str, Any] | None


class JsonRpcRequestSerializer(Protocol):
    """Protocol for JSON-RPC request objects that can serialize themselves."""

    def to_json(self) -> str:
        """Serialize the request to JSON."""
        ...


class JsonRpcRequest(PydanticModel):
    """Base Pydantic JSON-RPC request model."""

    jsonrpc: Literal["2.0"] = "2.0"
    id: JsonRpcId = 1
    method: str
    params: JsonRpcParams = None

    def to_json(
        self,
        *,
        indent: int | None = None,
        ensure_ascii: bool = False,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
        exclude_computed_fields: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
        polymorphic_serialization: bool | None = None,
    ) -> str:
        """Serialize the request to JSON."""
        return self.model_dump_json(
            indent=indent,
            ensure_ascii=ensure_ascii,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_computed_fields=exclude_computed_fields,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
            polymorphic_serialization=polymorphic_serialization,
        )


class JsonRpcErrorCode(IntEnum):
    """Known JSON-RPC and Solana RPC error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_BLOCK_CLEANED_UP = -32001
    SERVER_ERROR_SEND_TRANSACTION_PREFLIGHT_FAILURE = -32002
    SERVER_ERROR_TRANSACTION_SIGNATURE_VERIFICATION_FAILURE = -32003
    SERVER_ERROR_BLOCK_NOT_AVAILABLE = -32004
    SERVER_ERROR_NODE_UNHEALTHY = -32005
    SERVER_ERROR_TRANSACTION_PRECOMPILE_VERIFICATION_FAILURE = -32006
    SERVER_ERROR_SLOT_SKIPPED = -32007
    SERVER_ERROR_NO_SNAPSHOT = -32008
    SERVER_ERROR_LONG_TERM_STORAGE_SLOT_SKIPPED = -32009
    SERVER_ERROR_KEY_EXCLUDED_FROM_SECONDARY_INDEX = -32010
    SERVER_ERROR_TRANSACTION_HISTORY_NOT_AVAILABLE = -32011
    SCAN_ERROR = -32012
    SERVER_ERROR_TRANSACTION_SIGNATURE_LEN_MISMATCH = -32013
    SERVER_ERROR_BLOCK_STATUS_NOT_AVAILABLE_YET = -32014
    SERVER_ERROR_UNSUPPORTED_TRANSACTION_VERSION = -32015
    SERVER_ERROR_MIN_CONTEXT_SLOT_NOT_REACHED = -32016
    SERVER_ERROR_EPOCH_REWARDS_PERIOD_ACTIVE = -32017
    SERVER_ERROR_SLOT_NOT_EPOCH_BOUNDARY = -32018
    SERVER_ERROR_LONG_TERM_STORAGE_UNREACHABLE = -32019
    SERVER_ERROR_FILTER_TRANSACTION_NOT_FOUND = -32020
    SERVER_ERROR_NO_SLOT_HISTORY = -32021


class JsonRpcErrorObject(PydanticModel):
    """JSON-RPC error object."""

    code: int
    message: str
    data: Any | None = None


class SolanaJsonRpcError(Exception):
    """Raised when a Pydantic-owned JSON-RPC response contains an error."""

    def __init__(
        self,
        code: int,
        message: str,
        data: Any | None = None,
        *,
        request_id: JsonRpcId = None,
        method: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize JSON-RPC error."""
        self.code = code
        self.message = message
        self.data = data
        self.request_id = request_id
        self.method = method
        self.name = name
        super().__init__(message)

    @classmethod
    def from_error_object(
        cls,
        error: JsonRpcErrorObject,
        *,
        request_id: JsonRpcId = None,
        method: str | None = None,
    ) -> "SolanaJsonRpcError":
        """Create an exception from a JSON-RPC error object."""
        name = _get_error_name(error.code)
        return cls(
            error.code,
            error.message,
            error.data,
            request_id=request_id,
            method=method,
            name=name,
        )


class JsonRpcErrorParser(Protocol):
    """Protocol for converting JSON-RPC error objects into exceptions."""

    def __call__(
        self,
        error: JsonRpcErrorObject,
        *,
        request_id: JsonRpcId = None,
        method: str | None = None,
    ) -> Exception:
        """Parse a JSON-RPC error object into an exception."""
        ...


def default_jsonrpc_error_parser(
    error: JsonRpcErrorObject,
    *,
    request_id: JsonRpcId = None,
    method: str | None = None,
) -> SolanaJsonRpcError:
    """Default JSON-RPC error parser."""
    return SolanaJsonRpcError.from_error_object(error, request_id=request_id, method=method)


class JsonRpcResponseEnvelope(PydanticModel):
    """JSON-RPC response envelope."""

    jsonrpc: Literal["2.0"]
    id: JsonRpcId = None
    result: Any | None = None
    error: JsonRpcErrorObject | None = None

    @model_validator(mode="after")
    def _validate_result_or_error(self) -> "JsonRpcResponseEnvelope":
        fields_set = self.model_fields_set
        has_result = "result" in fields_set
        has_error = "error" in fields_set and self.error is not None
        if has_result and has_error:
            raise ValueError("JSON-RPC response cannot include both result and error")
        if not has_result and not has_error:
            raise ValueError("JSON-RPC response must include either result or error")
        return self

    def unwrap_result(
        self,
        error_parser: JsonRpcErrorParser | None = None,
        *,
        method: str | None = None,
    ) -> Any:
        """Return the response result or raise a parsed JSON-RPC error."""
        if self.error is not None:
            parser = error_parser or default_jsonrpc_error_parser
            raise parser(self.error, request_id=self.id, method=method)
        return self.result


TResult = TypeVar("TResult", bound=BaseModel)


def _get_error_name(code: int) -> str | None:
    try:
        return JsonRpcErrorCode(code).name
    except ValueError:
        return None
