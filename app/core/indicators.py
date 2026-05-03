"""Pure technical indicators. No I/O. Inputs are lists of floats (closing prices)."""

from __future__ import annotations


def sma(closes: list[float], period: int) -> float | None:
    if period <= 0 or len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def ema(closes: list[float], period: int) -> float | None:
    if period <= 0 or len(closes) < period:
        return None
    k = 2 / (period + 1)
    seed = sum(closes[:period]) / period
    value = seed
    for price in closes[period:]:
        value = price * k + value * (1 - k)
    return value


def rsi(closes: list[float], period: int = 14) -> float | None:
    if period <= 0 or len(closes) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for prev, curr in zip(closes[:-1], closes[1:], strict=True):
        diff = curr - prev
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, loss in zip(gains[period:], losses[period:], strict=True):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def summarize(closes: list[float]) -> dict[str, float | None]:
    """Compact technical-indicator snapshot consumable by an LLM agent."""
    return {
        "last_close": closes[-1] if closes else None,
        "sma_20": sma(closes, 20),
        "sma_50": sma(closes, 50),
        "ema_12": ema(closes, 12),
        "ema_26": ema(closes, 26),
        "rsi_14": rsi(closes, 14),
    }
