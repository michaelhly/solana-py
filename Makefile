clean:
	rm -rf dist build _build __pycache__ *.egg-info

format:
	isort setup.py solana tests
	black --line-length=120 setup.py solana tests

lint:
	pydocstyle setup.py solana test
	flake8 setup.py solana tests
	mypy solana
	pylint --rcfile=.pylintrc setup.py solana tests

.PHONY: notebook
notebook:
	cd notebooks && PYTHONPATH=../ jupyter notebook

publish:
	make clean
	python setup.py sdist bdist_wheel
	twine upload dist/*

test-publish:
	make clean
	python setup.py sdist bdist_wheel
	twine upload -r testpypi dist/*

.PHONY: tests
tests:
	PYTHONPATH=./solana pytest -v

unit-tests:
	PYTHONPATH=./solana pytest -v -m "not integration"

int-tests:
	PYTHONPATH=./solana pytest -v -m integration

# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docsrc
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: docs
docs:
	@make html
	@cp -a _build/html/ docs
