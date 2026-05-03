from app.core.quality import assess
from app.core.types import ExtractedDocument, ExtractedSection, ExtractedTable


def _doc(**kwargs) -> ExtractedDocument:
    base = dict(source_name="t.pdf", markdown="", sections=[], tables=[], page_count=0)
    base.update(kwargs)
    return ExtractedDocument(**base)


def test_no_text_flags_error() -> None:
    signals = assess(_doc(page_count=3, markdown=""))
    assert any(s.code == "no_text" and s.severity == "error" for s in signals)


def test_low_text_yield_flags_warning() -> None:
    signals = assess(_doc(page_count=10, markdown="just a few words on a long doc"))
    assert any(s.code == "low_text_yield" and s.severity == "warning" for s in signals)


def test_flat_structure_flags_info_when_long_no_headings() -> None:
    body = "Lots of text. " * 200
    signals = assess(
        _doc(
            page_count=8,
            markdown=body,
            sections=[
                ExtractedSection(
                    heading=None, level=0, heading_path=[], text=body, page_start=1, page_end=8
                )
            ],
        )
    )
    assert any(s.code == "flat_structure" for s in signals)


def test_sparse_table_flags_warning() -> None:
    table = ExtractedTable(
        index=0,
        page=2,
        rows=[["A", "B", "C"], ["", "", ""], ["", "", ""]],
    )
    signals = assess(_doc(page_count=2, markdown="text " * 100, tables=[table]))
    assert any(s.code == "sparse_table" for s in signals)


def test_degenerate_table_flagged() -> None:
    tiny = ExtractedTable(index=0, page=1, rows=[["x"]])
    signals = assess(_doc(page_count=1, markdown="ok " * 100, tables=[tiny]))
    assert any(s.code == "degenerate_table" for s in signals)


def test_clean_doc_returns_ok_signal() -> None:
    body = "Lots of meaningful text. " * 200
    sections = [
        ExtractedSection(
            heading="Intro", level=2, heading_path=["Intro"], text=body, page_start=1, page_end=2
        )
    ]
    signals = assess(_doc(page_count=2, markdown=body, sections=sections))
    assert signals and signals[0].code == "ok"
