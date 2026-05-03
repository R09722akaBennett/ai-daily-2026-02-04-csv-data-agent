"""Append-only JSONL store for decisions, outcomes, lessons, and traces.

Per-cycle artifacts live under ``<data_dir>/`` so a fresh run is one ``rm -rf data``.
Each record carries a UTC ``ts`` so consumers can order without reading the clock.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class JsonlStore:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.data_dir / f"{name}.jsonl"

    def append(self, name: str, record: dict[str, Any]) -> dict[str, Any]:
        record = {"id": record.get("id") or uuid.uuid4().hex[:12], "ts": _now_iso(), **record}
        path = self._path(name)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        # `os.O_APPEND` makes concurrent writes line-atomic on POSIX; fine for our single-process use.
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return record

    def read_all(self, name: str) -> list[dict[str, Any]]:
        path = self._path(name)
        if not path.exists():
            return []
        out: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if raw:
                    out.append(json.loads(raw))
        return out

    def read_recent(self, name: str, limit: int) -> list[dict[str, Any]]:
        rows = self.read_all(name)
        return rows[-limit:] if limit > 0 else rows


def default_store() -> JsonlStore:
    return JsonlStore(os.getenv("DATA_DIR", "./data"))
