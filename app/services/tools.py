"""Tool schemas + dispatcher for the five-agent team.

Each tool has a JSON schema Anthropic understands and a handler that takes
``(ctx, args)``. ``ctx`` is the ``ToolContext`` the orchestrator provides per cycle
so tools can read shared state (Binance client, memory store, current decision).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.core import indicators
from app.core.memory import JsonlStore
from app.services.market_data import BinanceClient, is_usdt_spot, top_movers


@dataclass
class ToolContext:
    binance: BinanceClient
    memory: JsonlStore
    cycle_id: str
    proposed_decision: dict[str, Any] | None = None
    risk_verdict: dict[str, Any] | None = None
    recorded_lesson: dict[str, Any] | None = None
    log: list[dict[str, Any]] = field(default_factory=list)


ToolHandler = Callable[[ToolContext, dict[str, Any]], dict[str, Any]]


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


def _h_get_top_gainers(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit", 10))
    return {
        "by": "priceChangePercent",
        "rows": top_movers(ctx.binance, by="priceChangePercent", limit=limit),
    }


def _h_get_top_volume(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit", 10))
    return {"by": "quoteVolume", "rows": top_movers(ctx.binance, by="quoteVolume", limit=limit)}


def _h_get_24h_stats(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    symbol = str(args["symbol"]).upper()
    raw = ctx.binance.ticker_24h(symbol)
    keep = ("symbol", "lastPrice", "priceChangePercent", "quoteVolume", "highPrice", "lowPrice")
    return {k: raw[k] for k in keep if k in raw}


def _h_compute_indicators(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    symbol = str(args["symbol"]).upper()
    interval = str(args.get("interval", "1h"))
    limit = int(args.get("limit", 100))
    closes = ctx.binance.closes(symbol, interval=interval, limit=limit)
    return {
        "symbol": symbol,
        "interval": interval,
        "samples": len(closes),
        "indicators": indicators.summarize(closes),
    }


def _h_read_lessons(ctx: ToolContext, _args: dict[str, Any]) -> dict[str, Any]:
    rows = ctx.memory.read_all("lessons")
    return {
        "count": len(rows),
        "lessons": [{"text": r.get("text"), "ts": r.get("ts")} for r in rows],
    }


def _h_read_recent_decisions(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit", 5))
    rows = ctx.memory.read_recent("decisions", limit)
    return {"count": len(rows), "decisions": rows}


def _h_read_outcomes(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit", 5))
    rows = ctx.memory.read_recent("outcomes", limit)
    return {"count": len(rows), "outcomes": rows}


def _h_propose_decision(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    symbol = str(args.get("symbol", "")).upper()
    action = str(args.get("action", "")).upper()
    size_pct = float(args.get("size_pct", 0.0))
    reasoning = str(args.get("reasoning", ""))
    if action not in ("BUY", "HOLD"):
        return {"error": f"action must be BUY or HOLD, got {action!r}"}
    if action == "HOLD":
        size_pct = 0.0
        symbol = symbol or "NONE"
    elif not is_usdt_spot(symbol):
        return {"error": f"symbol {symbol!r} is not a USDT-quoted spot pair"}
    decision = {
        "cycle_id": ctx.cycle_id,
        "symbol": symbol,
        "action": action,
        "size_pct": size_pct,
        "reasoning": reasoning,
    }
    ctx.proposed_decision = decision
    return {"recorded": True, "decision": decision}


def _h_validate_decision(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    approved = bool(args.get("approved", False))
    reason = str(args.get("reason", ""))
    if ctx.proposed_decision is None:
        return {"error": "no proposed decision to validate"}
    verdict = {"cycle_id": ctx.cycle_id, "approved": approved, "reason": reason}
    ctx.risk_verdict = verdict
    return {"recorded": True, "verdict": verdict}


def _h_record_lesson(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    text = str(args.get("text", "")).strip()
    if not text:
        return {"error": "lesson text cannot be empty"}
    lesson = {"cycle_id": ctx.cycle_id, "text": text}
    ctx.recorded_lesson = lesson
    return {"recorded": True, "lesson": lesson}


GET_TOP_GAINERS = Tool(
    name="get_top_gainers",
    description="Return the top USDT-quoted spot pairs ranked by 24h price change percent.",
    input_schema={
        "type": "object",
        "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}},
        "required": [],
    },
    handler=_h_get_top_gainers,
)
GET_TOP_VOLUME = Tool(
    name="get_top_volume",
    description="Return the top USDT-quoted spot pairs ranked by 24h quote volume.",
    input_schema={
        "type": "object",
        "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}},
        "required": [],
    },
    handler=_h_get_top_volume,
)
GET_24H_STATS = Tool(
    name="get_24h_stats",
    description="Get 24h price/volume stats for a single USDT-quoted spot symbol (e.g. BTCUSDT).",
    input_schema={
        "type": "object",
        "properties": {"symbol": {"type": "string", "description": "e.g. BTCUSDT"}},
        "required": ["symbol"],
    },
    handler=_h_get_24h_stats,
)
COMPUTE_INDICATORS = Tool(
    name="compute_indicators",
    description="Fetch klines and compute SMA(20/50), EMA(12/26), RSI(14) for a symbol.",
    input_schema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "interval": {"type": "string", "default": "1h", "enum": ["15m", "1h", "4h", "1d"]},
            "limit": {"type": "integer", "minimum": 50, "maximum": 500, "default": 100},
        },
        "required": ["symbol"],
    },
    handler=_h_compute_indicators,
)
READ_LESSONS = Tool(
    name="read_lessons",
    description="Read all lessons learned by past cycles (newest last).",
    input_schema={"type": "object", "properties": {}, "required": []},
    handler=_h_read_lessons,
)
READ_RECENT_DECISIONS = Tool(
    name="read_recent_decisions",
    description="Read the most recent decisions made by the team.",
    input_schema={
        "type": "object",
        "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5}},
        "required": [],
    },
    handler=_h_read_recent_decisions,
)
READ_OUTCOMES = Tool(
    name="read_outcomes",
    description="Read recent paper-trading outcomes (P&L for resolved decisions).",
    input_schema={
        "type": "object",
        "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5}},
        "required": [],
    },
    handler=_h_read_outcomes,
)
PROPOSE_DECISION = Tool(
    name="propose_decision",
    description=(
        "Trader's terminal tool. Submit the cycle's final trade decision. action must be BUY "
        "or HOLD. size_pct is percent of portfolio (HOLD => 0). Call this exactly once."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "action": {"type": "string", "enum": ["BUY", "HOLD"]},
            "size_pct": {"type": "number", "minimum": 0, "maximum": 100},
            "reasoning": {"type": "string"},
        },
        "required": ["action", "reasoning"],
    },
    handler=_h_propose_decision,
)
VALIDATE_DECISION = Tool(
    name="validate_decision",
    description="Risk's terminal tool. Approve or reject the Trader's proposed decision.",
    input_schema={
        "type": "object",
        "properties": {
            "approved": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["approved", "reason"],
    },
    handler=_h_validate_decision,
)
RECORD_LESSON = Tool(
    name="record_lesson",
    description="Reflector's terminal tool. Record exactly one lesson for future cycles.",
    input_schema={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
    handler=_h_record_lesson,
)


def dispatch(
    ctx: ToolContext, name: str, args: dict[str, Any], tools: list[Tool]
) -> dict[str, Any]:
    by_name = {t.name: t for t in tools}
    tool = by_name.get(name)
    if tool is None:
        return {"error": f"unknown tool: {name}"}
    try:
        result = tool.handler(ctx, args)
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}
    ctx.log.append({"tool": name, "args": args, "result": result})
    return result
