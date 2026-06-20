"""Shared Pydantic base model for solana-py data models."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

_T = TypeVar("_T", bound="PydanticModel")


class PydanticModel(BaseModel):
    """Base class for solana-py Pydantic models.

    These models are the successors to the deprecated ``NamedTuple`` types. They are
    configured to:

    - allow arbitrary types, so fields can hold non-Pydantic objects such as the
      solders ``Pubkey``/``Keypair`` types;
    - be immutable (``frozen``), matching the ``NamedTuple`` types they replace;
    - read field descriptions from attribute docstrings, so the documentation that
      previously lived next to ``NamedTuple`` fields is preserved.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
        use_attribute_docstrings=True,
    )

    @classmethod
    def from_namedtuple(cls: type[_T], value: Any) -> _T:
        """Coerce the deprecated ``NamedTuple`` equivalent into this Pydantic model.

        The deprecated ``NamedTuple`` types and these models share the same field names,
        so conversion is a straightforward field-by-field copy via ``NamedTuple._asdict``.

        If ``value`` is already an instance of this model it is returned unchanged, which
        makes this safe to call at API boundaries that accept either the deprecated
        ``NamedTuple`` or the new model.

        Args:
            value: A deprecated ``NamedTuple`` instance (or an existing instance of this
                model).

        Returns:
            An instance of this model.
        """
        if isinstance(value, cls):
            return value
        return cls(**value._asdict())
