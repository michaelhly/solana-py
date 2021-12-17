clean:
	rm -rf dist build _build __pycache__ *.egg-info

format:
	poetry run isort src tests
	poetry run black --line-length=120 src tests

lint:
	poetry run black --check --diff --line-length=120 src tests
	poetry run pydocstyle src tests
	poetry run flake8 src tests
	poetry run mypy src
	poetry run pylint --rcfile=.pylintrc src tests

publish:
	make clean
	poetry build
	poetry publish

test-publish:
	make clean
	poetry build
	poetry publish -r testpypi

.PHONY: tests
tests:
	poetry run pytest -vv

unit-tests:
	poetry run pytest -vv -m "not integration"

int-tests:
	poetry run pytest -vv -m integration

update-localnet:
	sh bin/localnet.sh update

start-localnet:
	sh bin/localnet.sh up

stop-localnet:
	sh bin/localnet.sh down

# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
