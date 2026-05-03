"""Single-agent runtime: manual Claude tool-use loop with prompt caching + trace."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import anthropic

from app.services.tools import Tool, ToolContext, dispatch


@dataclass
class AgentResult:
    role: str
    final_text: str
    turns: int
    usage: dict[str, int] = field(default_factory=dict)
    tool_log: list[dict[str, Any]] = field(default_factory=list)
    stop_reason: str | None = None


def _accumulate_usage(usage: dict[str, int], delta: Any) -> None:
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    ):
        value = getattr(delta, key, 0) or 0
        usage[key] = usage.get(key, 0) + int(value)


def _supports_thinking(model: str) -> bool:
    """Adaptive thinking is supported on Opus 4.6/4.7 and Sonnet 4.6 only."""
    return model.startswith(("claude-opus-4-7", "claude-opus-4-6", "claude-sonnet-4-6"))


def _supports_effort(model: str) -> bool:
    """Effort is supported on Opus 4.5+ and Sonnet 4.6 (not Haiku)."""
    return model.startswith(
        ("claude-opus-4-7", "claude-opus-4-6", "claude-opus-4-5", "claude-sonnet-4-6")
    )


def run_agent(
    *,
    client: anthropic.Anthropic,
    role: str,
    model: str,
    system_prompt: str,
    tools: list[Tool],
    user_message: str,
    ctx: ToolContext,
    max_turns: int = 8,
    max_tokens: int = 4096,
) -> AgentResult:
    tool_schemas = [t.schema() for t in tools]
    # Cache the (frozen) system prompt + tool list for this role; subsequent cycles within the
    # 5-minute window read instead of re-uploading the prompt.
    system_blocks = [
        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
    ]
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]

    create_kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_blocks,
        "tools": tool_schemas,
    }
    if _supports_thinking(model):
        create_kwargs["thinking"] = {"type": "adaptive"}
    if _supports_effort(model):
        # Opus models do the heavy reasoning; Sonnet stays at medium.
        create_kwargs["output_config"] = {
            "effort": "high" if model.startswith("claude-opus") else "medium"
        }

    usage: dict[str, int] = {}
    final_text = ""
    stop_reason: str | None = None
    turns = 0

    for turn in range(1, max_turns + 1):
        turns = turn
        response = client.messages.create(messages=messages, **create_kwargs)
        _accumulate_usage(usage, response.usage)
        stop_reason = response.stop_reason

        text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        if text_blocks:
            final_text = "\n".join(text_blocks).strip()

        tool_uses = [b for b in response.content if getattr(b, "type", None) == "tool_use"]
        if not tool_uses or stop_reason != "tool_use":
            break

        # Echo assistant turn (preserve tool_use blocks) and answer every tool call before looping.
        messages.append(
            {"role": "assistant", "content": [b.model_dump() for b in response.content]}
        )
        tool_results: list[dict[str, Any]] = []
        for use in tool_uses:
            result = dispatch(ctx, use.name, dict(use.input), tools)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": use.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return AgentResult(
        role=role,
        final_text=final_text,
        turns=turns,
        usage=usage,
        tool_log=list(ctx.log),
        stop_reason=stop_reason,
    )
