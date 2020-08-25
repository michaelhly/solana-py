.PHONY: format
format:
	black --check --diff --line-length=120 solana tests

.PHONY: lint 
lint:
	pydocstyle solana tests
	flake8 solana tests
	mypy solana
	pylint --rcfile=.pylintrc solana tests

.PHONY: notebook
notebook:
	cd notebooks && PYTHONPATH=../solana jupyter notebook

.PHONY: tests
tests:
	PYTHONPATH=./solana pytest -v

unit-tests:
	PYTHONPATH=./solana pytest -v -m "not integration"

int-tests:
	PYTHONPATH=./solana pytest -v -m integration
