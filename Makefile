.PHONY: format
format:
	black --check --diff --line-length=120 src tests

.PHONY: lint 
lint:
	pydocstyle src tests
	flake8 src tests
	mypy src tests
	pylint --rcfile=.pylintrc src tests

.PHONY: notebook
notebook:
	cd notebooks && PYTHONPATH=../src jupyter notebook

.PHONY: test
test:
	PYTHONPATH=./src pytest
