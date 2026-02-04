from __future__ import annotations

from fastapi import FastAPI

from app.core.config import Settings
from app.core.logging import configure_logging
from app.web.app_factory import create_app


def build_app() -> FastAPI:
    settings = Settings()
    configure_logging(settings)
    return create_app(settings)


app = build_app()
