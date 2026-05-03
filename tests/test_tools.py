from pathlib import Path
from typing import Any

import pytest

from app.core.memory import JsonlStore
from app.services import tools as tools_mod
from app.services.tools import ToolContext, dispatch


class FakeBinance:
    """Just enough surface for the tools we call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def ticker_24h(self, symbol: str | None = None) -> Any:
        if symbol is None:
            return [
                {
                    "symbol": "BTCUSDT",
                    "lastPrice": "70000",
                    "priceChangePercent": "5.0",
                    "quoteVolume": "1e9",
                },
                {
                    "symbol": "DOGEUPUSDT",
                    "lastPrice": "1",
                    "priceChangePercent": "20.0",
                    "quoteVolume": "1e6",
                },
                {
                    "symbol": "ETHUSDT",
                    "lastPrice": "3500",
                    "priceChangePercent": "1.0",
                    "quoteVolume": "5e8",
                },
            ]
        return {
            "symbol": symbol,
            "lastPrice": "100",
            "priceChangePercent": "2.5",
            "quoteVolume": "1e7",
            "highPrice": "110",
            "lowPrice": "90",
        }

    def closes(self, symbol: str, interval: str = "1h", limit: int = 100) -> list[float]:
        self.calls.append(("closes", (symbol, interval, limit)))
        return [float(x) for x in range(1, limit + 1)]


@pytest.fixture()
def ctx(tmp_path: Path) -> ToolContext:
    memory = JsonlStore(str(tmp_path))
    return ToolContext(binance=FakeBinance(), memory=memory, cycle_id="cycle-1")  # type: ignore[arg-type]


def test_get_top_gainers_filters_leveraged_tokens(ctx: ToolContext) -> None:
    out = dispatch(ctx, "get_top_gainers", {"limit": 10}, [tools_mod.GET_TOP_GAINERS])
    symbols = [r["symbol"] for r in out["rows"]]
    assert "DOGEUPUSDT" not in symbols
    assert symbols[0] == "BTCUSDT"  # highest priceChangePercent among non-leveraged


def test_compute_indicators_round_trip(ctx: ToolContext) -> None:
    out = dispatch(
        ctx,
        "compute_indicators",
        {"symbol": "btcusdt", "limit": 60},
        [tools_mod.COMPUTE_INDICATORS],
    )
    assert out["symbol"] == "BTCUSDT"
    assert out["samples"] == 60
    assert out["indicators"]["last_close"] == 60.0


def test_propose_decision_validates_action(ctx: ToolContext) -> None:
    bad = dispatch(
        ctx,
        "propose_decision",
        {"symbol": "BTCUSDT", "action": "SELL", "size_pct": 5, "reasoning": "..."},
        [tools_mod.PROPOSE_DECISION],
    )
    assert "error" in bad
    assert ctx.proposed_decision is None


def test_propose_decision_hold_zeroes_size(ctx: ToolContext) -> None:
    out = dispatch(
        ctx,
        "propose_decision",
        {"symbol": "", "action": "HOLD", "size_pct": 99, "reasoning": "no setup"},
        [tools_mod.PROPOSE_DECISION],
    )
    assert out["recorded"] is True
    assert ctx.proposed_decision is not None
    assert ctx.proposed_decision["size_pct"] == 0.0


def test_record_lesson_rejects_empty(ctx: ToolContext) -> None:
    out = dispatch(ctx, "record_lesson", {"text": "  "}, [tools_mod.RECORD_LESSON])
    assert "error" in out
    assert ctx.recorded_lesson is None


def test_unknown_tool_returns_error(ctx: ToolContext) -> None:
    out = dispatch(ctx, "no_such_tool", {}, [tools_mod.RECORD_LESSON])
    assert "error" in out
