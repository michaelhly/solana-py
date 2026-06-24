"""Shared Pydantic base model for solana-py data models."""

from __future__ import annotations


from pydantic import BaseModel, ConfigDict


class PydanticModel(BaseModel):
    """Base class for solana-py Pydantic models.

    Shared behavior for all solana-py data models.

    Models are configured to:

    - allow arbitrary types, so fields can hold non-Pydantic objects such as the
      solders ``Pubkey``/``Keypair`` types;
        - be immutable (``frozen``);
        - read field descriptions from attribute docstrings.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True, use_attribute_docstrings=True)
