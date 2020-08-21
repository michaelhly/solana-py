.PHONY: lint 
lint:
	mypy src tests
	pylint --rcfile=.pylintrc src tests

.PHONY: notebook
notebook:
	cd notebooks && PYTHONPATH=../src jupyter notebook

.PHONY: test
test:
	PYTHONPATH=./src pytest
