.. solana.py documentation master file, created by
   sphinx-quickstart on Mon Aug 24 23:50:00 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

.. image:: https://img.shields.io/pypi/v/solana?color=blue
   :alt: PyPI version
   :target: https://pypi.org/project/solana/

.. image:: https://img.shields.io/pypi/pyversions/solana?color=blue
   :alt: PyPI pyversions
   :target: https://pypi.org/project/solana/

.. image:: https://codecov.io/gh/michaelhly/solana-py/branch/master/graph/badge.svg
   :alt: Codecov
   :target: https://codecov.io/gh/michaelhly/solana-py/branch/master

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :alt: License
   :target: https://github.com/michaelhly/solana-py/blob/master/LICENSE

Solana.py is the Python API for interfacing with the `Solana JSON RPC <https://docs.solana.com/developing/clients/jsonrpc-api/>`_.

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

Async API Client:

.. highlight:: py
.. code-block:: py

    import asyncio
    from solana.rpc.async_api import AsyncClient

    async def main():
        async with AsyncClient("https://api.devnet.solana.com") as client:
            res = await client.is_connected()
        print(res)  # True

        # Alternatively, close the client explicitly instead of using a context manager:
        client = AsyncClient("https://api.devnet.solana.com")
        res = await client.is_connected()
        print(res)  # True
        await client.close()

    asyncio.run(main())


Websockets Client:

.. note::
    The websockets code in solana-py is mostly just wrapping around the `websockets <https://websockets.readthedocs.io/en/stable/index.html>`_ library.

.. highlight:: py
.. code-block:: py

    import asyncio
    from asyncstdlib import enumerate
    from solana.rpc.websocket_api import connect

    async def main():
        async with connect("ws://api.devnet.solana.com") as websocket:
            await websocket.logs_subscribe()
            first_resp = await websocket.recv()
            subscription_id = first_resp.result
            next_resp = await websocket.recv()
            print(next_resp)
            await websocket.logs_unsubscribe(subscription_id)

        # Alternatively, use the client as an infinite asynchronous iterator:
        async with connect("ws://api.devnet.solana.com") as websocket:
            await websocket.logs_subscribe()
            first_resp = await websocket.recv()
            subscription_id = first_resp.result
            async for idx, msg in enumerate(websocket):
                if idx == 3:
                    break
                print(msg)
            await websocket.logs_unsubscribe(subscription_id)

    asyncio.run(main())

Additional Resources
--------------------

Check out `anchorpy <https://kevinheavey.github.io/anchorpy/>`_, a Python client for `Anchor
<https://project-serum.github.io/anchor/getting-started/introduction.html>`_ based programs on Solana.



.. toctree::
   :maxdepth: 4
   :caption: Contents:

   self
   api
   solana
   spl


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
