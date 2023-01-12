clean:
	rm -rf dist build __pycache__ *.egg-info

format:
	poetry run black src tests

lint:
	poetry run black --check --diff src tests
	poetry run ruff src tests
	poetry run mypy src

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
	poetry run pytest -vv -m "not integration" --doctest-modules

int-tests:
	poetry run pytest -vv -m integration

update-localnet:
	sh bin/localnet.sh update

start-localnet:
	sh bin/localnet.sh up

stop-localnet:
	sh bin/localnet.sh down

serve:
	mkdocs serve

