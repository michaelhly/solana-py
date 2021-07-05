"""Solana.py is the Python API for interfacing with the `Solana JSON RPC <https://docs.solana.com/developing/clients/jsonrpc-api/>`_.

Installation
------------

.. highlight:: sh
.. code-block:: sh

    pip install solana

Usage
-----

General usage:

.. highlight:: py
.. code-block:: py

    import solana

API Client:

.. highlight:: py
.. code-block:: py

    from solana.rpc.api import Client

    http_client = Client("https://api.devnet.solana.com")

"""  # pylint: disable=line-too-long # noqa: E501
import sys

if sys.version_info < (3, 7):
    raise EnvironmentError("Python 3.7 or above is required.")
