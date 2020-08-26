# Solana.py

Solana Python API built on the [JSON RPC API](https://docs.solana.com/apps/jsonrpc-api).

Python version of [solana-web3.js](https://github.com/solana-labs/solana-web3.js/) for interacting with Solana.

Read the [Documentation](https://michaelhly.github.io/solanapy/).

## Quickstart

### Installation

```sh
pip install solana
```

### General Usage

```py
import solana
```

### API Client

```py
from solana.rpc.api import HTTP, WEBSOCKET, Client

http_client = Client(endpoint="https://devnet.solana.com", client_type=HTTP)
websocket_client = Client(endpoint="ws://localhost:8900", client_type=WEBSOCKET)
```

## Development

### Setup

1. Install pipenv.

```sh
brew install pipenv
```

2. Install dev dependencies.

```sh
pipenv install --dev
```

3. Activate the pipenv shell.

```sh
pipenv shell
```

### Lint

```sh
make lint
```

### Tests

```sh
# All tests
make tests
# Unit tests only
make unit-tests
# Integration tests only
make int-tests
```

### Start a Solana Localnet

Install [docker](https://docs.docker.com/get-started/).

```sh
# Update/pull latest docker image
pipenv run update-localnet
# Start localnet instance
pipenv run start-localnet
```

### Using Jupyter Notebook

```sh
make notebook
```
