"""Run a single decision cycle: Scout -> Analyst x N -> Trader -> Risk -> (maybe) Reflector."""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

import anthropic

from app.core.config import Settings
from app.core.memory import JsonlStore
from app.services.agent import AgentResult, run_agent
from app.services.market_data import BinanceClient, is_usdt_spot
from app.services.team import AgentSpec, make_team
from app.services.tools import ToolContext


@dataclass
class CycleReport:
    cycle_id: str
    candidates: list[str]
    analyst_memos: dict[str, str] = field(default_factory=dict)
    decision: dict[str, Any] | None = None
    risk_verdict: dict[str, Any] | None = None
    lesson: dict[str, Any] | None = None
    agent_runs: list[dict[str, Any]] = field(default_factory=list)
    total_usage: dict[str, int] = field(default_factory=dict)


def _parse_picks(text: str) -> list[str]:
    """Extract `PICKS: A, B, C` line; fall back to scanning USDT-quoted tokens."""
    match = re.search(r"PICKS\s*:\s*([^\n]+)", text, re.IGNORECASE)
    candidates_line = match.group(1) if match else text
    raw = re.findall(r"[A-Z0-9]{2,}USDT", candidates_line.upper())
    seen: list[str] = []
    for symbol in raw:
        if symbol not in seen and is_usdt_spot(symbol):
            seen.append(symbol)
    return seen[:5]


def _accumulate(total: dict[str, int], delta: dict[str, int]) -> None:
    for key, value in delta.items():
        total[key] = total.get(key, 0) + value


def _record_run(report: CycleReport, spec: AgentSpec, result: AgentResult) -> None:
    report.agent_runs.append(
        {
            "role": spec.role,
            "model": spec.model,
            "turns": result.turns,
            "stop_reason": result.stop_reason,
            "usage": result.usage,
            "final_text": result.final_text,
            "tool_log": result.tool_log,
        }
    )
    _accumulate(report.total_usage, result.usage)


def run_cycle(
    *,
    settings: Settings,
    binance: BinanceClient,
    memory: JsonlStore,
    client: anthropic.Anthropic,
    reflect: bool = False,
) -> CycleReport:
    cycle_id = uuid.uuid4().hex[:10]
    team = make_team(settings)
    report = CycleReport(cycle_id=cycle_id, candidates=[])

    # 1) Scout — pick candidates.
    scout_ctx = ToolContext(binance=binance, memory=memory, cycle_id=cycle_id)
    scout = team["scout"]
    scout_result = run_agent(
        client=client,
        role=scout.role,
        model=scout.model,
        system_prompt=scout.system_prompt,
        tools=scout.tools,
        user_message="Pick 3-5 USDT-quoted spot symbols worth analyzing this cycle. Use your tools.",
        ctx=scout_ctx,
    )
    _record_run(report, scout, scout_result)
    report.candidates = _parse_picks(scout_result.final_text)
    if not report.candidates:
        return report  # nothing to analyze; abort early.

    # 2) Analyst — one memo per candidate.
    for symbol in report.candidates:
        analyst_ctx = ToolContext(binance=binance, memory=memory, cycle_id=cycle_id)
        analyst = team["analyst"]
        memo_result = run_agent(
            client=client,
            role=f"analyst:{symbol}",
            model=analyst.model,
            system_prompt=analyst.system_prompt,
            tools=analyst.tools,
            user_message=f"Write a technical memo for {symbol} on the 1h timeframe.",
            ctx=analyst_ctx,
        )
        _record_run(report, analyst, memo_result)
        report.analyst_memos[symbol] = memo_result.final_text

    # 3) Trader — one decision based on the memos.
    trader_ctx = ToolContext(binance=binance, memory=memory, cycle_id=cycle_id)
    trader = team["trader"]
    memos_block = "\n\n".join(
        f"=== {sym} ===\n{memo}" for sym, memo in report.analyst_memos.items()
    )
    trader_result = run_agent(
        client=client,
        role=trader.role,
        model=trader.model,
        system_prompt=trader.system_prompt,
        tools=trader.tools,
        user_message=(
            "Analyst memos for this cycle's candidates are below. Read past lessons, then call "
            "propose_decision exactly once.\n\n" + memos_block
        ),
        ctx=trader_ctx,
    )
    _record_run(report, trader, trader_result)
    report.decision = trader_ctx.proposed_decision
    if report.decision is None:
        return report  # trader never proposed; nothing to validate.

    # 4) Risk — gate.
    risk_ctx = ToolContext(
        binance=binance, memory=memory, cycle_id=cycle_id, proposed_decision=report.decision
    )
    risk = team["risk"]
    risk_result = run_agent(
        client=client,
        role=risk.role,
        model=risk.model,
        system_prompt=risk.system_prompt,
        tools=risk.tools,
        user_message=(
            "Validate this proposed decision against the rules. Call validate_decision exactly once.\n\n"
            f"DECISION: {report.decision}"
        ),
        ctx=risk_ctx,
    )
    _record_run(report, risk, risk_result)
    report.risk_verdict = risk_ctx.risk_verdict

    # 5) Persist decision (always — including HOLDs, useful for behavior research).
    memory.append("decisions", {**report.decision, "risk": report.risk_verdict})

    # 6) Reflector — optional, every Nth cycle (caller decides).
    if reflect:
        reflector_ctx = ToolContext(binance=binance, memory=memory, cycle_id=cycle_id)
        reflector = team["reflector"]
        reflector_result = run_agent(
            client=client,
            role=reflector.role,
            model=reflector.model,
            system_prompt=reflector.system_prompt,
            tools=reflector.tools,
            user_message="Read recent decisions, outcomes, and lessons. Record one lesson.",
            ctx=reflector_ctx,
        )
        _record_run(report, reflector, reflector_result)
        if reflector_ctx.recorded_lesson is not None:
            memory.append("lessons", reflector_ctx.recorded_lesson)
            report.lesson = reflector_ctx.recorded_lesson

    return report


def report_to_dict(report: CycleReport) -> dict[str, Any]:
    return asdict(report)
