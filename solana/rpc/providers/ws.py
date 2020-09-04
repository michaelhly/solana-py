"""WebSocket RPC provider."""
# https://github.com/ethereum/web3.py/blob/d431db5fcaa3d624e8361a99ae3317b82367fe65/web3/providers/websocket.py#L83
import asyncio
import itertools
import json
import logging
import os
import websockets  # type: ignore

from threading import Thread
from types import TracebackType
from typing import Any, Optional, Type, Union, cast


from .._utils.encoding import FriendlyJsonSerde
from ..types import URI, RPCMethod, RPCResponse
from .base import BaseProvider

RESTRICTED_WEBSOCKET_KWARGS = {"uri", "loop"}
DEFAULT_WEBSOCKET_TIMEOUT = 10


def get_default_endpoint() -> URI:
    """Get the default ws rpc endpoint."""
    return URI(os.environ.get("SOLANA_WS_PROVIDER_URI", "ws://localhost:8900"))


def _start_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Start event loop."""
    asyncio.set_event_loop(loop)
    loop.run_forever()
    loop.close()


def _get_threaded_loop() -> asyncio.AbstractEventLoop:
    """Get threaded loop."""
    new_loop = asyncio.new_event_loop()
    thread_loop = Thread(target=_start_event_loop, args=(new_loop,), daemon=True)
    thread_loop.start()
    return new_loop


class PersistentWebSocket:
    """Sets up a persistent websocket."""

    logger = logging.getLogger("solana.providers.PersistentWebSocket")

    def __init__(self, endpoint_uri: URI, loop: asyncio.AbstractEventLoop, websocket_kwargs: Any) -> None:
        """Initialize persistent websocket."""
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.endpoint_uri = endpoint_uri
        self.loop = loop
        self.websocket_kwargs = websocket_kwargs

    async def __aenter__(self) -> websockets.WebSocketClientProtocol:
        """Connect the websocket."""
        if self.ws is None:
            self.ws = await websockets.connect(uri=self.endpoint_uri, loop=self.loop, **self.websocket_kwargs)
        return self.ws

    async def __aexit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
        """Close the websocket."""
        if self.ws is not None and exc_val is not None:
            try:
                await self.ws.close()
            except Exception as err:
                self.logger.debug("Exception caught on exit: %s", str(err))
            self.ws = None


class WSProvider(BaseProvider, FriendlyJsonSerde):
    """WSProvider class for websockets."""

    logger = logging.getLogger("solana.providers.WebsocketProvider")
    _loop = None

    def __init__(
        self,
        endpoint_uri: Union[URI, str],
        websocket_kwargs: Optional[Any] = None,
        websocket_timeout: int = DEFAULT_WEBSOCKET_TIMEOUT,
    ) -> None:
        """Initialize the websocket provider."""
        self._request_counter = itertools.count()
        if isinstance(endpoint_uri, str):
            self.endpoint_uri = URI(endpoint_uri)
        else:
            self.endpoint_uri = endpoint_uri
        self.websocket_timeout = websocket_timeout
        if self.endpoint_uri is None:
            self.endpoint_uri = get_default_endpoint()
        if WSProvider._loop is None:
            WSProvider._loop = _get_threaded_loop()
        if websocket_kwargs is None:
            websocket_kwargs = {}
        else:
            found_restricted_keys = set(websocket_kwargs.keys()).intersection(RESTRICTED_WEBSOCKET_KWARGS)
            if found_restricted_keys:
                raise Exception(
                    "{0} are not allowed in websocket_kwargs, "
                    "found: {1}".format(RESTRICTED_WEBSOCKET_KWARGS, found_restricted_keys)
                )
        self.conn = PersistentWebSocket(self.endpoint_uri, WSProvider._loop, websocket_kwargs)

    def __str__(self) -> str:
        """Return a string representation of the websocket connection."""
        return "WS connection {0}".format(self.endpoint_uri)

    async def coro_make_request(self, request_data: bytes) -> RPCResponse:
        """Makes coroutine requests."""
        try:
            async with self.conn as conn:
                await asyncio.wait_for(conn.send(request_data), timeout=self.websocket_timeout)
                return json.loads(await asyncio.wait_for(conn.recv(), timeout=self.websocket_timeout))
        except TimeoutError:
            self.logger.debug("Websocket connection timed out.")
            raise
        except Exception as err:
            self.logger.debug("Unexpected Exception: %s", err)
            raise

    def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make a request to the rpc endpoint."""
        request_id = next(self._request_counter) + 1
        self.logger.debug("Making request WebSocket URI: %s, Method: %s, id: %s", self.endpoint_uri, method, request_id)
        request_data = self.json_encode({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        if WSProvider._loop:
            future = asyncio.run_coroutine_threadsafe(
                self.coro_make_request(cast(bytes, request_data)), WSProvider._loop
            )
        return future.result()

    def connection(self) -> Optional[websockets.WebSocketClientProtocol]:
        """Exposes the websocket connection."""
        return self.conn.ws

    def is_connected(self) -> bool:
        """Health check."""
        try:
            if WSProvider._loop is not None:
                future = asyncio.run_coroutine_threadsafe(self.coro_make_request(bytes()), WSProvider._loop)
                future.result(timeout=self.websocket_timeout)
                return True
        except asyncio.TimeoutError:
            self.logger.debug("Websocket connection timed out.")
        return False
