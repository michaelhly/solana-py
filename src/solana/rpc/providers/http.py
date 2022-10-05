"""HTTP RPC Provider."""
from typing import Any, Optional, Union

from based58 import b58encode
import requests

from ...exceptions import SolanaRpcException, handle_exceptions
from ..types import RPCMethod, RPCResponse
from .base import BaseProvider
from .core import _HTTPProviderCore


class HTTPProvider(BaseProvider, _HTTPProviderCore):
    """HTTP provider to interact with the http rpc endpoint."""

    def __str__(self) -> str:
        """String definition for HTTPProvider."""
        return f"HTTP RPC connection {self.endpoint_uri}"

    @handle_exceptions(SolanaRpcException, requests.exceptions.RequestException)
    def make_request(
        self, method: RPCMethod, *params: Any, header_opt: Optional[dict] = None
    ) -> Union[RPCResponse, requests.Response]:
        """Make a HTTP request to a http rpc endpoint."""
        request_kwargs = self._before_request(method=method, params=params, is_async=False)

        if header_opt:
            headers = request_kwargs["headers"]
            data = request_kwargs["data"].encode("utf-8")
            authorization_values = []

            if "authority_pair" in header_opt:
                data_authority_signature = header_opt["authority_pair"].sign(data)
                authorization_values.append(
                    f"authority:{header_opt['authority_pair'].public_key}="
                    f"{b58encode(bytes(data_authority_signature)).decode('utf-8')}"
                )

            if "identity_pair" in header_opt:
                data_identity_signature = header_opt["identity_pair"].sign(data)
                authorization_values.append(
                    f"identity:{header_opt['identity_pair'].public_key}="
                    f"{b58encode(bytes(data_identity_signature)).decode('utf-8')}"
                )

            headers.update({"authorization": ",".join(authorization_values)})

        raw_response = requests.post(**request_kwargs, timeout=self.timeout)
        if raw_response.status_code == 200:
            return self._after_request(raw_response=raw_response, method=method)
        else:
            return raw_response

    def is_connected(self) -> bool:
        """Health check."""
        try:
            response = requests.get(self.health_uri)
            response.raise_for_status()
        except (IOError, requests.HTTPError) as err:
            self.logger.error("Health check failed with error: %s", str(err))
            return False

        return response.ok
