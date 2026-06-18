"""Exceptions native to solana-py."""

from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class SolanaExceptionBase(Exception):
    """Base class for Solana-py exceptions."""

    def __init__(self, exc: Exception, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Init."""
        self.error_msg = self._build_error_message(exc, func, *args, **kwargs)
        super().__init__(self.error_msg)

    @staticmethod
    def _build_error_message(
        exc: Exception,
        func: Callable[..., Any],
        *args: Any,  # noqa: ARG004
        **kwargs: Any,  # noqa: ARG004
    ) -> str:
        return f"{type(exc)} raised in {func} invokation"


class SolanaRpcException(SolanaExceptionBase):
    """Class for Solana-py RPC exceptions."""

    @staticmethod
    def _build_error_message(
        exc: Exception,
        func: Callable[..., Any],  # noqa: ARG004
        *args: Any,
        **kwargs: Any,  # noqa: ARG004
    ) -> str:
        rpc_method = args[1].__class__.__name__
        return f'{type(exc)} raised in "{rpc_method}" endpoint request'


def handle_exceptions(
    internal_exception_cls: type[SolanaRpcException],
    *exception_types_caught: type[Exception],
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for handling non-async exception."""

    def func_decorator(func: Callable[P, T]) -> Callable[P, T]:
        def argument_decorator(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except exception_types_caught as exc:
                raise internal_exception_cls(exc, func, *args, **kwargs) from exc

        return argument_decorator

    return func_decorator


def handle_async_exceptions(
    internal_exception_cls: type[SolanaRpcException],
    *exception_types_caught: type[Exception],
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """Decorator for handling async exception."""

    def func_decorator(
        func: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        async def argument_decorator(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except exception_types_caught as exc:
                raise internal_exception_cls(exc, func, *args, **kwargs) from exc

        return argument_decorator

    return func_decorator
