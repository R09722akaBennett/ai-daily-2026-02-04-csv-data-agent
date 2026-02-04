# CSV Data Agent

FastAPI + Streamlit service for repeatable CSV profiling steps.

## Why this project

A productized data-agent starts with deterministic preprocessing. This service profiles CSV columns (non-empty/unique counts) as a baseline tool inside a larger agent workflow.

## Inspiration / Sources

- Python csv module — https://docs.python.org/3/library/csv.html

## Architecture

- FastAPI backend: `app/` (app factory + routers + services + core domain)
- Streamlit UI: `app/web/streamlit_app.py`

## Run (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Terminal A (API):

```bash
API_PORT=8204 ./scripts/dev_api.sh
```

Terminal B (UI):

```bash
UI_API_URL=http://127.0.0.1:8204 streamlit run app/web/streamlit_app.py --server.port 8604
```

## Smoke test

```bash
curl -s http://127.0.0.1:8204/api/health | python3 -m json.tool
```

## Roadmap (Next steps)

- Add persistence (SQLite) where applicable
- Add auth + rate limiting
- Add background jobs + queue for long-running tasks
- Add Docker + deployment target
