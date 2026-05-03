"""Thin adapter around Docling.

Lazy import: importing this module is cheap. Docling is loaded only when
``run_docling()`` is actually called. ``is_available()`` lets the rest of the
service degrade to demo-mode without raising.
"""

from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any

from app.core.types import ExtractedDocument, ExtractedSection, ExtractedTable


def is_available() -> bool:
    """True iff `docling` can be imported in this process."""
    try:
        importlib.import_module("docling.document_converter")
    except Exception:
        return False
    return True


def _build_converter(do_table_structure: bool, do_ocr: bool) -> Any:
    """Build a Docling DocumentConverter with table/OCR options. Lazy import inside."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pdf_opts = PdfPipelineOptions()
    pdf_opts.do_ocr = do_ocr
    pdf_opts.do_table_structure = do_table_structure

    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts)},
    )


def _table_to_rows(tbl: Any) -> list[list[str]]:
    """Best-effort row extraction across Docling minor versions.

    Newer Docling exposes `tbl.export_to_dataframe()`; we fall back to walking
    `tbl.data.table_cells` (cell objects with row_offset / col_offset) so this
    keeps working when pandas isn't installed.
    """
    if hasattr(tbl, "export_to_dataframe"):
        try:
            df = tbl.export_to_dataframe()
            return [[str(x) if x is not None else "" for x in row] for row in df.values.tolist()]
        except Exception:
            pass
    cells = getattr(getattr(tbl, "data", None), "table_cells", None) or []
    if not cells:
        return []
    max_row = max((c.start_row_offset_idx for c in cells), default=-1)
    max_col = max((c.start_col_offset_idx for c in cells), default=-1)
    grid: list[list[str]] = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]
    for c in cells:
        r, col = c.start_row_offset_idx, c.start_col_offset_idx
        if 0 <= r <= max_row and 0 <= col <= max_col:
            grid[r][col] = (c.text or "").strip()
    return grid


def _heading_walk(doc: Any) -> list[ExtractedSection]:
    """Collapse Docling text items into heading-aware sections."""
    sections: list[ExtractedSection] = []
    current_heading: str | None = None
    current_level: int = 0
    current_path: list[str] = []
    buffer: list[str] = []
    page_start = 0
    page_end = 0

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            sections.append(
                ExtractedSection(
                    heading=current_heading,
                    level=current_level,
                    heading_path=list(current_path),
                    text=text,
                    page_start=page_start,
                    page_end=page_end,
                )
            )

    for item in getattr(doc, "texts", []) or []:
        label = getattr(item, "label", "")
        text = (getattr(item, "text", "") or "").strip()
        if not text:
            continue
        page = 0
        provs = getattr(item, "prov", None) or []
        if provs:
            page = getattr(provs[0], "page_no", 0) or 0

        if str(label).startswith("section_header") or str(label) == "title":
            flush()
            buffer = []
            level = int(getattr(item, "level", 1) or 1)
            current_path = current_path[: level - 1] + [text]
            current_heading = text
            current_level = level
            page_start = page_end = page or page_end
        else:
            buffer.append(text)
            if page:
                page_start = page_start or page
                page_end = page

    flush()
    return sections


def run_docling(
    *,
    source_path: Path,
    source_name: str,
    do_table_structure: bool = True,
    do_ocr: bool = True,
    max_pages: int | None = None,
) -> ExtractedDocument:
    """Convert one file into an ``ExtractedDocument``.

    Raises ``RuntimeError`` if Docling isn't installed — caller should check
    ``is_available()`` first or catch the error and fall back to demo mode.
    """
    if not is_available():
        raise RuntimeError(
            "docling is not installed. Run `pip install -e '.[extract]'` to enable extraction."
        )

    started = time.monotonic()
    converter = _build_converter(do_table_structure=do_table_structure, do_ocr=do_ocr)

    convert_kwargs: dict[str, Any] = {}
    if max_pages:
        convert_kwargs["max_num_pages"] = max_pages
    result = converter.convert(str(source_path), **convert_kwargs)
    doc = result.document

    markdown = ""
    if hasattr(doc, "export_to_markdown"):
        markdown = doc.export_to_markdown()

    tables: list[ExtractedTable] = []
    for idx, tbl in enumerate(getattr(doc, "tables", []) or []):
        rows = _table_to_rows(tbl)
        page = 0
        provs = getattr(tbl, "prov", None) or []
        if provs:
            page = getattr(provs[0], "page_no", 0) or 0
        caption = None
        get_caption = getattr(tbl, "caption_text", None)
        if callable(get_caption):
            try:
                caption = (get_caption() or "").strip() or None
            except Exception:
                caption = None
        tables.append(ExtractedTable(index=idx, page=page, rows=rows, caption=caption))

    sections = _heading_walk(doc)

    page_count = 0
    pages = getattr(doc, "pages", None)
    if isinstance(pages, dict):
        page_count = len(pages)
    elif hasattr(pages, "__len__"):
        page_count = len(pages)

    elapsed_ms = int((time.monotonic() - started) * 1000)
    return ExtractedDocument(
        source_name=source_name,
        markdown=markdown,
        sections=sections,
        tables=tables,
        page_count=page_count,
        metadata={
            "format": getattr(result, "input", {}).format if hasattr(result, "input") else None
        },
        warnings=[],
        extractor={
            "engine": "docling",
            "elapsed_ms": elapsed_ms,
            "options": {
                "do_table_structure": do_table_structure,
                "do_ocr": do_ocr,
                "max_pages": max_pages,
            },
        },
    )
