.PHONY: lint 
lint:
	pydocstyle --ignore=D401,D203,D213 src tests
	mypy src tests
	pylint --rcfile=.pylintrc src tests

.PHONY: notebook
notebook:
	cd notebooks && PYTHONPATH=../src jupyter notebook

.PHONY: test
test:
	PYTHONPATH=./src pytest
