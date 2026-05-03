.PHONY: dev-api dev-ui dev-web web-install web-build test lint

dev-api:
	./scripts/dev_api.sh

dev-ui:                # Streamlit (internal QA)
	./scripts/dev_ui.sh

dev-web:               # Next.js (external demo / GTM surface)
	npm --prefix web run dev

web-install:
	npm --prefix web install

web-build:
	npm --prefix web run build

test:
	PYTHONPATH=. pytest

lint:
	ruff check . --exclude web
