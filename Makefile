clean:
	rm -rf dist build __pycache__ *.egg-info

format:
	uv run ruff format src tests

lint:
	uv run ruff format --check --diff src tests
	uv run ruff check src tests
	uv run mypy src

publish: clean
	uv build
	uv publish

test-publish: clean
	uv build
	uv publish --publish-url https://test.pypi.org/legacy/

tests:
	uv run pytest

tests-parallel:
	uv run pytest -n auto

unit-tests:
	uv run pytest -m "not integration" --doctest-modules

int-tests:
	uv run pytest -m integration

update-localnet:
	./bin/localnet.sh update

start-localnet:
	./bin/localnet.sh up

stop-localnet:
	./bin/localnet.sh down

serve:
	mkdocs serve

.PHONY: $(MAKECMDGOALS)
