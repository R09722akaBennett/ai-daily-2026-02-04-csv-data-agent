"""Shared FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

import anthropic
from fastapi import HTTPException

from app.core.config import Settings
from app.core.memory import JsonlStore
from app.services.market_data import BinanceClient


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_memory() -> JsonlStore:
    return JsonlStore(get_settings().data_dir)


def get_binance() -> BinanceClient:
    return BinanceClient(base_url=get_settings().binance_base_url)


def get_anthropic() -> anthropic.Anthropic:
    api_key = get_settings().anthropic_api_key.strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured. Set it in .env to run cycles.",
        )
    return anthropic.Anthropic(api_key=api_key)
