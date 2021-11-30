"""Friendly JSON serializer & deserializer for Requests."""
import collections.abc
import json
from typing import Any, Dict, Iterable, Optional, Type


# Original source:
# https://github.com/ethereum/web3.py/blob/8bb0b56f65f1ab96b46db79f9956517ac628bd7b/web3/_utils/encoding.py#L181
class FriendlyJsonSerde:
    """Friendly JSON serializer & deserializer.

    When encoding or decoding fails, this class collects
    information on which fields failed, to show more
    helpful information in the raised error messages.
    """

    def _json_mapping_errors(self, mapping: Dict[Any, Any]) -> Iterable[str]:
        for key, val in mapping.items():
            try:
                self._friendly_json_encode(val)
            except TypeError as exc:
                yield f"{key}: because ({exc})"

    def _json_list_errors(self, iterable: Iterable[Any]) -> Iterable[str]:
        for index, element in enumerate(iterable):
            try:
                self._friendly_json_encode(element)
            except TypeError as exc:
                yield f"{index}: because ({exc})"

    @staticmethod
    def _is_list_like(obj: Any) -> bool:
        return not isinstance(obj, (bytes, str, bytearray)) and isinstance(obj, collections.abc.Sequence)

    def _friendly_json_encode(self, obj: Dict[Any, Any], cls: Optional[Type[json.JSONEncoder]] = None) -> str:
        try:
            encoded = json.dumps(obj, cls=cls)
            return encoded
        except TypeError as full_exception:
            if hasattr(obj, "items"):
                item_errors = "; ".join(self._json_mapping_errors(obj))
                raise TypeError(f"dict had unencodable value at keys: {{{item_errors}}}") from full_exception
            if FriendlyJsonSerde._is_list_like(obj):
                element_errors = "; ".join(self._json_list_errors(obj))
                raise TypeError(f"list had unencodable value at index: [{element_errors}]") from full_exception
            raise full_exception

    def json_decode(self, json_str: str) -> Dict[Any, Any]:  # pylint: disable=no-self-use
        """Deserialize JSON document to a Python object with friendly error messages."""
        try:
            decoded = json.loads(json_str)
            return decoded
        except json.decoder.JSONDecodeError as exc:
            err_msg = f"Could not decode {repr(json_str)} because of {exc}."
            # Calling code may rely on catching JSONDecodeError to recognize bad json
            # so we have to re-raise the same type.
            raise json.decoder.JSONDecodeError(err_msg, exc.doc, exc.pos)

    def json_encode(self, obj: Dict[Any, Any], cls: Optional[Type[json.JSONEncoder]] = None) -> str:
        """Serialize obj to a JSON formatted `str` with friendly error messages."""
        try:
            return self._friendly_json_encode(obj, cls=cls)
        except TypeError as exc:
            raise TypeError("Could not encode to JSON") from exc
