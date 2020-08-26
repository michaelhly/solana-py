"""Solana.py is the Python API for interfacing with the `Solana JSON RPC <https://docs.solana.com/apps/jsonrpc-api/>`_.

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

    from solana.rpc.api import HTTP, WEBSOCKET, Client

    http_client = Client(endpoint="https://devnet.solana.com", client_type=HTTP)
    websocket_client = Client(endpoint="ws://localhost:8900", client_type=WEBSOCKET)

"""
