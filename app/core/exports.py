"""Export profiles — the actual handover surface for downstream tools.

Each exporter produces a stable, documented shape so a customer's RAG /
spreadsheet / DB pipeline can depend on it.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Any

from app.core.types import ExtractedDocument, RagChunk


def to_markdown(doc: ExtractedDocument) -> str:
    return doc.markdown or ""


def to_full_json(doc: ExtractedDocument) -> dict[str, Any]:
    """Deterministic JSON of the whole extraction. Field names mirror types.py."""
    payload = {
        "source_name": doc.source_name,
        "page_count": doc.page_count,
        "metadata": doc.metadata,
        "extractor": doc.extractor,
        "warnings": [asdict(w) for w in doc.warnings],
        "sections": [asdict(s) for s in doc.sections],
        "tables": [
            {
                "index": t.index,
                "page": t.page,
                "n_rows": t.n_rows,
                "n_cols": t.n_cols,
                "has_header": t.has_header,
                "caption": t.caption,
                "rows": t.rows,
            }
            for t in doc.tables
        ],
        "markdown": doc.markdown,
    }
    return payload


def table_to_csv(rows: list[list[str]]) -> str:
    """Serialize a 2D table to CSV text (RFC 4180-ish via stdlib)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def to_table_csvs(doc: ExtractedDocument) -> dict[str, str]:
    """Return {filename: csv_text} for each extracted table."""
    out: dict[str, str] = {}
    for tbl in doc.tables:
        slug = f"table-{tbl.index:02d}-p{tbl.page or 0:03d}.csv"
        out[slug] = table_to_csv(tbl.rows)
    return out


def to_rag_jsonl(chunks: list[RagChunk]) -> str:
    """One JSON object per line — drop straight into a vector-DB ingest job."""
    lines = [
        json.dumps(
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "metadata": {
                    "source_name": c.source_name,
                    "heading_path": c.heading_path,
                    "page_start": c.page_start,
                    "page_end": c.page_end,
                    "token_estimate": c.token_estimate,
                },
            },
            ensure_ascii=False,
        )
        for c in chunks
    ]
    return "\n".join(lines) + ("\n" if lines else "")
