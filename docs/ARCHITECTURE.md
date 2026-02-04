# Architecture

## Layers

- `app/main.py`: entrypoint; loads Settings, configures logging, builds FastAPI app.
- `app/web/app_factory.py`: app factory (middleware, router wiring).
- `app/api/`: HTTP layer (routers + request/response models).
- `app/schemas/`: Pydantic models shared by API routes.
- `app/services/`: orchestration layer (calls core + db/external APIs).
- `app/core/`: domain rules (the part that should differ *every day*).

## Daily project rule

**Boilerplate is allowed in web/api/config/logging only.**

Every daily project must implement at least:
- A domain module under `app/core/<project>.py` with pure functions/classes
- A router under `app/api/v1/routes/<project>.py`
- Tests for the domain rules under `tests/test_<project>.py`

This prevents “copy a template and rename” projects.
