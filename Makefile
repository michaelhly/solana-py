clean:
	rm -rf dist build _build __pycache__ *.egg-info

format:
	pipenv run isort setup.py solana spl tests
	pipenv run black --line-length=120 setup.py solana spl tests

lint:
	pipenv run pydocstyle setup.py solana spl/**/*.py test
	pipenv run flake8 setup.py solana spl tests
	pipenv run mypy solana
	pipenv run mypy --namespace-packages --explicit-package-bases spl
	pipenv run pylint --rcfile=.pylintrc setup.py solana spl tests

.PHONY: notebook
notebook:
	cd notebooks && PYTHONPATH=../ jupyter notebook

publish:
	make clean
	python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*

test-publish:
	make clean
	python setup.py sdist bdist_wheel
	pipenv run twine upload -r testpypi dist/*

.PHONY: tests
tests:
	pipenv run pytest -vv

unit-tests:
	pipenv run pytest -vv -m "not integration"

int-tests:
	pipenv run pytest -vv -m integration

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
