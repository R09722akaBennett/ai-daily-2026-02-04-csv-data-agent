"""End-to-end orchestrator test with a fake Anthropic client.

The fake client returns scripted responses driven by the system prompt — that's how we
recognize which agent is calling. This is enough to verify the cycle's flow control
without paying for real Claude calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.core.config import Settings
from app.core.memory import JsonlStore
from app.services.orchestrator import run_cycle


class FakeBinance:
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
        return [float(x) for x in range(1, limit + 1)]


def _content_text(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        type="text", text=text, model_dump=lambda: {"type": "text", "text": text}
    )


def _content_tool_use(tool_id: str, name: str, args: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        type="tool_use",
        id=tool_id,
        name=name,
        input=args,
        model_dump=lambda: {"type": "tool_use", "id": tool_id, "name": name, "input": args},
    )


def _response(content: list[SimpleNamespace], stop_reason: str) -> SimpleNamespace:
    return SimpleNamespace(
        content=content,
        stop_reason=stop_reason,
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=20,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )


class FakeMessages:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        system_text = kwargs["system"][0]["text"]
        # Once a tool_result has been observed, the agent's next call should be allowed to
        # end the loop — otherwise the fake would loop forever.
        has_tool_result = any(
            isinstance(m["content"], list)
            and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"])
            for m in kwargs["messages"]
        )
        if has_tool_result:
            return _response([_content_text("done")], stop_reason="end_turn")
        # Dispatch on the unique "You are the X" preamble of each role's prompt.
        if "You are the Scout" in system_text:
            return _response(
                [
                    _content_text(
                        "PICKS: BTCUSDT, ETHUSDT\nREASONS:\n- BTCUSDT: vol\n- ETHUSDT: trend"
                    )
                ],
                stop_reason="end_turn",
            )
        if "You are the Analyst" in system_text:
            user_msg = kwargs["messages"][0]["content"]
            symbol = "BTCUSDT" if "BTCUSDT" in user_msg else "ETHUSDT"
            return _response(
                [
                    _content_text(
                        f"SYMBOL: {symbol}\nPRICE: 100\nTREND: bull\nRSI: 55\nTHESIS: ok\nRISKS: meh"
                    )
                ],
                stop_reason="end_turn",
            )
        if "You are the Trader" in system_text:
            return _response(
                [
                    _content_tool_use(
                        "tu_trader",
                        "propose_decision",
                        {
                            "symbol": "BTCUSDT",
                            "action": "BUY",
                            "size_pct": 10,
                            "reasoning": "clean trend",
                        },
                    )
                ],
                stop_reason="tool_use",
            )
        if "You are the Risk" in system_text:
            return _response(
                [
                    _content_tool_use(
                        "tu_risk", "validate_decision", {"approved": True, "reason": "within rules"}
                    )
                ],
                stop_reason="tool_use",
            )
        if "You are the Reflector" in system_text:
            return _response(
                [
                    _content_tool_use(
                        "tu_ref", "record_lesson", {"text": "Re-check RSI on BUY signals."}
                    )
                ],
                stop_reason="tool_use",
            )
        return _response([_content_text("?")], stop_reason="end_turn")


class FakeAnthropic:
    def __init__(self) -> None:
        self.messages = FakeMessages()


def test_run_cycle_happy_path(tmp_path: Path) -> None:
    settings = Settings(data_dir=str(tmp_path))
    memory = JsonlStore(str(tmp_path))
    binance = FakeBinance()
    client = FakeAnthropic()

    report = run_cycle(
        settings=settings,
        binance=binance,  # type: ignore[arg-type]
        memory=memory,
        client=client,  # type: ignore[arg-type]
        reflect=True,
    )

    assert report.candidates == ["BTCUSDT", "ETHUSDT"]
    assert set(report.analyst_memos.keys()) == {"BTCUSDT", "ETHUSDT"}
    assert report.decision == {
        "cycle_id": report.cycle_id,
        "symbol": "BTCUSDT",
        "action": "BUY",
        "size_pct": 10.0,
        "reasoning": "clean trend",
    }
    assert report.risk_verdict == {
        "cycle_id": report.cycle_id,
        "approved": True,
        "reason": "within rules",
    }
    assert report.lesson is not None and "RSI" in report.lesson["text"]

    decisions = memory.read_all("decisions")
    assert decisions[-1]["action"] == "BUY"
    assert decisions[-1]["risk"]["approved"] is True

    lessons = memory.read_all("lessons")
    assert lessons[-1]["text"] == "Re-check RSI on BUY signals."

    # 1 scout + 2 analysts + 1 trader (2 turns) + 1 risk (2 turns) + 1 reflector (2 turns) = 9 calls
    assert len(client.messages.calls) == 9
    # Trader's terminal-tool-call response was answered before loop ended:
    trader_calls = [
        c for c in client.messages.calls if "You are the Trader" in c["system"][0]["text"]
    ]
    assert len(trader_calls) == 2
    # Second trader call must include the prior tool_use + tool_result roundtrip:
    second = trader_calls[1]
    assert second["messages"][1]["role"] == "assistant"
    assert second["messages"][2]["role"] == "user"
    assert json.loads(second["messages"][2]["content"][0]["content"])["recorded"] is True


def test_run_cycle_aborts_when_scout_returns_no_picks(tmp_path: Path) -> None:
    settings = Settings(data_dir=str(tmp_path))
    memory = JsonlStore(str(tmp_path))

    class EmptyScoutMessages(FakeMessages):
        def create(self, **kwargs: Any) -> Any:
            return _response(
                [_content_text("PICKS: \nREASONS: nothing compelling")], stop_reason="end_turn"
            )

    client = SimpleNamespace(messages=EmptyScoutMessages())
    report = run_cycle(
        settings=settings,
        binance=FakeBinance(),  # type: ignore[arg-type]
        memory=memory,
        client=client,  # type: ignore[arg-type]
        reflect=False,
    )
    assert report.candidates == []
    assert report.decision is None
    assert memory.read_all("decisions") == []
