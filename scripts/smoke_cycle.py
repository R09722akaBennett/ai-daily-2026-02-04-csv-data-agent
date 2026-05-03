#!/usr/bin/env python3
"""End-to-end smoke test: runs one real cycle.

Requires ANTHROPIC_API_KEY in the environment (or .env). Spends real Anthropic tokens.
Run: PYTHONPATH=. python scripts/smoke_cycle.py
"""

from __future__ import annotations

import json
import sys

import anthropic

from app.core.config import Settings
from app.core.memory import JsonlStore
from app.services.market_data import BinanceClient
from app.services.orchestrator import report_to_dict, run_cycle


def main() -> int:
    settings = Settings()
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY is not set. Aborting.", file=sys.stderr)
        return 1
    memory = JsonlStore(settings.data_dir)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    with BinanceClient(base_url=settings.binance_base_url) as binance:
        report = run_cycle(
            settings=settings, binance=binance, memory=memory, client=client, reflect=False
        )
    print(json.dumps(report_to_dict(report), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
