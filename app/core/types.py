"""Internal IDP types — the contract every layer reads/writes against.

We deliberately do NOT expose Docling's `DoclingDocument` outside `docling_runner`,
so the rest of the codebase (tests, exports, API, UI) keeps working when Docling
isn't installed. The runner's job is to translate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["info", "warning", "error"]


@dataclass
class ExtractedTable:
    index: int  # 0-based, stable per document
    page: int  # 1-based page number; 0 when unknown
    rows: list[list[str]]  # row-major (header row included if present)
    has_header: bool = True
    caption: str | None = None
    note: str | None = None  # e.g. "merged cells flattened"

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        return max((len(r) for r in self.rows), default=0)

    @property
    def empty_cell_ratio(self) -> float:
        total = sum(len(r) for r in self.rows)
        if total == 0:
            return 0.0
        empty = sum(1 for r in self.rows for c in r if not (c or "").strip())
        return empty / total


@dataclass
class ExtractedSection:
    """One contiguous block of body text under a heading path."""

    heading: str | None  # nearest heading text, or None for preamble
    level: int  # H1=1, H2=2, ...; 0 for un-headed text
    heading_path: list[str]  # ancestors → leaf, e.g. ["Intro", "Background"]
    text: str
    page_start: int = 0
    page_end: int = 0


@dataclass
class QualitySignal:
    code: str  # stable, machine-checkable: e.g. "no_ocr_text"
    severity: Severity
    message: str  # human-friendly explanation
    suggestion: str | None = None  # what the user can do about it


@dataclass
class ExtractedDocument:
    source_name: str
    markdown: str
    sections: list[ExtractedSection] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    page_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[QualitySignal] = field(default_factory=list)
    # Free-form timing/tooling info; used by the UI's "trust" panel.
    extractor: dict[str, Any] = field(default_factory=dict)


@dataclass
class RagChunk:
    """One LLM-ready chunk with citation back to source pages + heading path."""

    chunk_id: str
    text: str
    heading_path: list[str]
    page_start: int
    page_end: int
    token_estimate: int
    source_name: str
