"""Exceptions native to solana-py."""
from typing import Any, Callable


class SolanaExceptionBase(Exception):
    """Base class for Solana-py exceptions."""

    def __init__(self, exc: Exception, func: Callable[[Any], Any], *args: Any, **kwargs: Any) -> None:
        """Init."""
        super().__init__()
        self.error_msg = self._build_error_message(exc, func, *args, **kwargs)

    @staticmethod
    def _build_error_message(
        exc: Exception, func: Callable[[Any], Any], *args: Any, **kwargs: Any  # pylint: disable=unused-argument
    ) -> str:
        return f"{type(exc)} raised in {func} invokation"


class SolanaRpcException(SolanaExceptionBase):
    """Class for Solana-py RPC exceptions."""

    @staticmethod
    def _build_error_message(exc: Exception, func: Callable[[Any], Any], *args: Any, **kwargs: Any) -> str:
        rpc_method = args[1].__class__.__name__
        return f'{type(exc)} raised in "{rpc_method}" endpoint request'


def handle_exceptions(internal_exception_cls, *exception_types_caught):
    """Decorator for handling non-async exception."""

    def func_decorator(func):
        def argument_decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types_caught as exc:
                raise internal_exception_cls(exc, func, *args, **kwargs) from exc

        return argument_decorator

    return func_decorator


def handle_async_exceptions(internal_exception_cls, *exception_types_caught):
    """Decorator for handling async exception."""

    def func_decorator(func):
        async def argument_decorator(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exception_types_caught as exc:
                raise internal_exception_cls(exc, func, *args, **kwargs) from exc

        return argument_decorator

    return func_decorator
