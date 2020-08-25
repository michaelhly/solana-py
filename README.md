# Solana.py

Solana Python API built on the [JSON RPC API](https://docs.solana.com/apps/jsonrpc-api).

## Development

### Setup

1. Install pipenv.

```sh
brew install pipenv
```

2. Install dependencies.

```sh
pipenv install
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

### Start a Solana localnet

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
