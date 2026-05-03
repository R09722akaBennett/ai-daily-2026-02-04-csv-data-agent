"""Heuristic quality signals.

These are surfaced to the user *before* they ship extraction output to a RAG
pipeline. The goal is to make silent failure modes loud — the #1 IDP user pain
point is "looks fine, then RAG hallucinates because half the doc was a scan".
"""

from __future__ import annotations

from app.core.types import ExtractedDocument, QualitySignal


def _word_count(text: str) -> int:
    return len(text.split())


def assess(doc: ExtractedDocument) -> list[QualitySignal]:
    signals: list[QualitySignal] = []

    body_words = _word_count(doc.markdown)

    if doc.page_count > 0 and body_words / max(doc.page_count, 1) < 30:
        signals.append(
            QualitySignal(
                code="low_text_yield",
                severity="warning",
                message=(
                    f"Only {body_words} words across {doc.page_count} page(s). "
                    "The document may be a scan with weak OCR, or mostly images."
                ),
                suggestion="Enable OCR (DOCLING_DO_OCR=true) or pre-process the PDF.",
            )
        )

    if doc.page_count > 0 and body_words == 0:
        signals.append(
            QualitySignal(
                code="no_text",
                severity="error",
                message="No text was extracted. The document is likely an image-only PDF or corrupt.",
                suggestion="Enable OCR or convert the file to a searchable PDF first.",
            )
        )

    headings = sum(1 for s in doc.sections if s.heading)
    if doc.page_count >= 5 and headings == 0:
        signals.append(
            QualitySignal(
                code="flat_structure",
                severity="info",
                message="No headings detected. RAG retrieval will rely on chunk position alone.",
                suggestion="Consider whether the source has headings that the layout model missed.",
            )
        )

    for table in doc.tables:
        if table.n_rows < 2 or table.n_cols < 2:
            signals.append(
                QualitySignal(
                    code="degenerate_table",
                    severity="warning",
                    message=(
                        f"Table #{table.index} on page {table.page} has shape "
                        f"{table.n_rows}x{table.n_cols} — likely not a real table."
                    ),
                    suggestion="Inspect the original — it may be a layout artifact rather than tabular data.",
                )
            )
            continue
        if table.empty_cell_ratio > 0.5:
            signals.append(
                QualitySignal(
                    code="sparse_table",
                    severity="warning",
                    message=(
                        f"Table #{table.index} on page {table.page} is "
                        f"{table.empty_cell_ratio:.0%} empty cells — extraction may have lost merged cells."
                    ),
                    suggestion="Spot-check the original layout; consider re-running with a different model.",
                )
            )

    if not signals:
        signals.append(
            QualitySignal(
                code="ok",
                severity="info",
                message="No structural issues detected.",
            )
        )
    return signals
