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
	cd notebooks && PYTHONPATH=../ jupyter notebook

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
