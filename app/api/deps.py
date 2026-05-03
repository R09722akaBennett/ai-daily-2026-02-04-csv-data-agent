"""Shared FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings
from app.services.jobs import JobStore, default_store


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_jobs() -> JobStore:
    return default_store()
