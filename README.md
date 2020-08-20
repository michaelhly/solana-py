# PySerum
Python client library for interacting with the Project Serum DEX.

# Development
## Setup
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

## Lint
```sh
pylint src
```

## Test
```sh
# pytest ...
```

## Using Jupyter Notebook
Run the following commands in your pipenv shell,
```sh
cd notebooks
PYTHONPATH=../src jupyter notebook
```
