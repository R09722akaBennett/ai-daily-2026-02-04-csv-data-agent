"""Binance public REST client. No API key. Sync httpx with a small in-memory cache."""

from __future__ import annotations

import time
from typing import Any

import httpx

_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_SECONDS = 30.0


def _cached_get(client: httpx.Client, path: str, params: dict[str, Any] | None = None) -> Any:
    key = f"{path}?{sorted((params or {}).items())}"
    now = time.monotonic()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < _TTL_SECONDS:
        return hit[1]
    response = client.get(path, params=params)
    response.raise_for_status()
    data = response.json()
    _CACHE[key] = (now, data)
    return data


class BinanceClient:
    def __init__(self, base_url: str = "https://api.binance.com", timeout: float = 10.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BinanceClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def ticker_24h(self, symbol: str | None = None) -> Any:
        params = {"symbol": symbol} if symbol else None
        return _cached_get(self._client, "/api/v3/ticker/24hr", params)

    def klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> list[list[Any]]:
        return _cached_get(
            self._client,
            "/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )

    def closes(self, symbol: str, interval: str = "1h", limit: int = 100) -> list[float]:
        return [float(row[4]) for row in self.klines(symbol, interval, limit)]


def is_usdt_spot(symbol: str) -> bool:
    """Reject leveraged tokens; accept plain USDT-quoted spot pairs."""
    if not symbol.endswith("USDT"):
        return False
    base = symbol[:-4]
    bad_suffixes = ("UP", "DOWN", "BULL", "BEAR")
    return not any(base.endswith(s) for s in bad_suffixes)


def top_movers(client: BinanceClient, *, by: str, limit: int = 10) -> list[dict[str, Any]]:
    """Top USDT-quoted spot pairs by ``priceChangePercent`` or ``quoteVolume``."""
    if by not in ("priceChangePercent", "quoteVolume"):
        raise ValueError(f"unsupported sort key: {by}")
    raw = client.ticker_24h()
    rows = [r for r in raw if is_usdt_spot(r["symbol"])]
    rows.sort(key=lambda r: float(r[by]), reverse=True)
    keep = ("symbol", "lastPrice", "priceChangePercent", "quoteVolume")
    return [{k: r[k] for k in keep} for r in rows[:limit]]
