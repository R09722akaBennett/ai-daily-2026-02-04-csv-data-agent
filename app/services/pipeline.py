"""Orchestrates: bytes-on-disk → ExtractedDocument → enriched with quality signals."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.core import docling_runner, quality
from app.core.config import Settings
from app.core.types import ExtractedDocument
from app.services.demo_fixture import build_demo_document


class ExtractionUnavailable(RuntimeError):
    """Raised when Docling isn't installed and demo mode is also disabled."""


def extract_bytes(
    *,
    settings: Settings,
    data: bytes,
    filename: str,
) -> ExtractedDocument:
    """Run extraction on a single file, returning an enriched document."""
    if not docling_runner.is_available():
        if settings.demo_mode:
            doc = build_demo_document()
            doc.source_name = filename or doc.source_name
            doc.warnings = quality.assess(doc)
            doc.extractor.setdefault("engine", "demo-fixture")
            doc.extractor["note"] = (
                "Docling is not installed — returned a demo fixture. "
                "Install with `pip install -e '.[extract]'` for real extraction."
            )
            return doc
        raise ExtractionUnavailable(
            "Docling is not installed and DEMO_MODE is disabled. "
            "Install with `pip install -e '.[extract]'` or set DEMO_MODE=true."
        )

    suffix = Path(filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as f:
        f.write(data)
        f.flush()
        doc = docling_runner.run_docling(
            source_path=Path(f.name),
            source_name=filename,
            do_table_structure=settings.docling_do_table_structure,
            do_ocr=settings.docling_do_ocr,
            max_pages=settings.docling_max_pages or None,
        )
    doc.warnings = quality.assess(doc)
    return doc
