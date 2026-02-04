from __future__ import annotations

import csv
import io
from dataclasses import dataclass


@dataclass
class ColumnProfile:
    name: str
    non_empty: int
    unique: int


def profile_csv(text: str) -> list[ColumnProfile]:
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    rows = list(reader)
    if not rows:
        return []

    cols = reader.fieldnames or []
    out: list[ColumnProfile] = []
    for c in cols:
        vals = [r.get(c) for r in rows]
        non_empty = sum(1 for v in vals if v not in (None, ''))
        unique = len(set(v for v in vals if v not in (None, '')))
        out.append(ColumnProfile(name=c, non_empty=non_empty, unique=unique))
    return out
