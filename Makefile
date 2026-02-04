.PHONY: dev-api dev-ui test lint

dev-api:
	./scripts/dev_api.sh

dev-ui:
	./scripts/dev_ui.sh

test:
	PYTHONPATH=./app pytest

lint:
	ruff check .
