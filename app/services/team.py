"""Agent factory: each role's (model, system prompt, tool set)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core import prompts
from app.core.config import Settings
from app.services import tools


@dataclass(frozen=True)
class AgentSpec:
    role: str
    model: str
    system_prompt: str
    tools: list[tools.Tool]


def make_team(settings: Settings) -> dict[str, AgentSpec]:
    return {
        "scout": AgentSpec(
            role="scout",
            model=settings.scout_model,
            system_prompt=prompts.SCOUT,
            tools=[tools.GET_TOP_GAINERS, tools.GET_TOP_VOLUME, tools.GET_24H_STATS],
        ),
        "analyst": AgentSpec(
            role="analyst",
            model=settings.analyst_model,
            system_prompt=prompts.ANALYST,
            tools=[tools.GET_24H_STATS, tools.COMPUTE_INDICATORS, tools.READ_LESSONS],
        ),
        "trader": AgentSpec(
            role="trader",
            model=settings.trader_model,
            system_prompt=prompts.TRADER,
            tools=[tools.READ_LESSONS, tools.READ_RECENT_DECISIONS, tools.PROPOSE_DECISION],
        ),
        "risk": AgentSpec(
            role="risk",
            model=settings.risk_model,
            system_prompt=prompts.RISK,
            tools=[tools.VALIDATE_DECISION],
        ),
        "reflector": AgentSpec(
            role="reflector",
            model=settings.reflector_model,
            system_prompt=prompts.REFLECTOR,
            tools=[
                tools.READ_LESSONS,
                tools.READ_RECENT_DECISIONS,
                tools.READ_OUTCOMES,
                tools.RECORD_LESSON,
            ],
        ),
    }
