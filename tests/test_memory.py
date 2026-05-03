from pathlib import Path

from app.core.memory import JsonlStore


def test_append_and_read(tmp_path: Path) -> None:
    store = JsonlStore(str(tmp_path))
    store.append("decisions", {"symbol": "BTCUSDT", "action": "BUY"})
    store.append("decisions", {"symbol": "ETHUSDT", "action": "HOLD"})
    rows = store.read_all("decisions")
    assert [r["symbol"] for r in rows] == ["BTCUSDT", "ETHUSDT"]
    assert all("ts" in r and "id" in r for r in rows)


def test_read_recent(tmp_path: Path) -> None:
    store = JsonlStore(str(tmp_path))
    for i in range(5):
        store.append("decisions", {"i": i})
    last_two = store.read_recent("decisions", 2)
    assert [r["i"] for r in last_two] == [3, 4]


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    store = JsonlStore(str(tmp_path))
    assert store.read_all("nope") == []
    assert store.read_recent("nope", 5) == []


def test_assigned_id_is_preserved(tmp_path: Path) -> None:
    store = JsonlStore(str(tmp_path))
    store.append("lessons", {"id": "fixed-id", "text": "always check RSI"})
    rows = store.read_all("lessons")
    assert rows[0]["id"] == "fixed-id"
