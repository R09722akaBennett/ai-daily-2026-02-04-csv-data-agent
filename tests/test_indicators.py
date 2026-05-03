from app.core import indicators


def test_sma_short_returns_none() -> None:
    assert indicators.sma([1, 2], 5) is None


def test_sma_basic() -> None:
    assert indicators.sma([1, 2, 3, 4, 5], 5) == 3.0
    assert indicators.sma([1, 2, 3, 4, 5], 3) == 4.0


def test_ema_seed_equals_sma_when_no_extra_data() -> None:
    closes = [1.0, 2.0, 3.0]
    # period == len: EMA = simple average of seed window
    assert indicators.ema(closes, 3) == 2.0


def test_ema_grows_with_uptrend() -> None:
    closes = [float(x) for x in range(1, 21)]  # 1..20 ascending
    seed_avg = sum(closes[:5]) / 5  # 3.0
    value = indicators.ema(closes, 5)
    assert value is not None
    # On an ascending series, EMA(period=5) should be well above the seed avg
    assert value > seed_avg


def test_rsi_pure_uptrend_is_100() -> None:
    closes = [float(x) for x in range(1, 30)]  # only gains
    assert indicators.rsi(closes, 14) == 100.0


def test_rsi_pure_downtrend_is_zero() -> None:
    closes = [float(x) for x in range(30, 1, -1)]  # only losses
    assert indicators.rsi(closes, 14) == 0.0


def test_summarize_shape() -> None:
    closes = [float(x) for x in range(1, 60)]
    snap = indicators.summarize(closes)
    assert set(snap.keys()) == {"last_close", "sma_20", "sma_50", "ema_12", "ema_26", "rsi_14"}
    assert snap["last_close"] == 59.0
