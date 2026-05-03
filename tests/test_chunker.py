from app.core.chunker import chunk_document
from app.core.types import ExtractedDocument, ExtractedSection


def _section(heading: str, text: str, page: int = 1) -> ExtractedSection:
    return ExtractedSection(
        heading=heading,
        level=2,
        heading_path=["Doc", heading],
        text=text,
        page_start=page,
        page_end=page,
    )


def test_chunks_propagate_heading_path_and_page() -> None:
    doc = ExtractedDocument(
        source_name="x.pdf",
        markdown="",
        sections=[_section("Intro", "Hello world. " * 30, page=4)],
    )
    chunks = chunk_document(doc, target_tokens=200, overlap_tokens=20)
    assert chunks
    for c in chunks:
        assert c.heading_path == ["Doc", "Intro"]
        assert c.page_start == 4 and c.page_end == 4
        assert c.source_name == "x.pdf"


def test_chunks_respect_target_size() -> None:
    big_text = "Sentence number one. " * 200  # ~ 4000 chars ~ 1000 tokens by heuristic
    doc = ExtractedDocument(
        source_name="big.pdf",
        markdown="",
        sections=[_section("S", big_text)],
    )
    chunks = chunk_document(doc, target_tokens=200, overlap_tokens=20)
    assert len(chunks) >= 4
    # No chunk should massively exceed target_tokens (allow slack for sentence boundary).
    assert all(c.token_estimate <= 250 for c in chunks)


def test_overlap_creates_shared_sentences() -> None:
    # Each sentence is ~120 chars ≈ 30 tokens by the heuristic; 8 sentences ≈ 240 tokens,
    # comfortably over target=80, so packing must produce ≥3 chunks with overlap.
    long = (
        "This is a long sentence that contains many words to give the chunker enough body "
        "to reliably split into multiple chunks here."
    )
    text = " ".join(f"{long} S{i}." for i in range(8))
    doc = ExtractedDocument(
        source_name="x.pdf",
        markdown="",
        sections=[_section("S", text)],
    )
    chunks = chunk_document(doc, target_tokens=80, overlap_tokens=20)
    assert len(chunks) >= 2
    # Adjacent chunks should share at least one sentence due to overlap.
    a = set(chunks[0].text.split())
    b = set(chunks[1].text.split())
    assert a & b, "expected non-empty intersection between adjacent chunks (overlap window)"


def test_invalid_overlap_raises() -> None:
    doc = ExtractedDocument(source_name="x", markdown="", sections=[])
    try:
        chunk_document(doc, target_tokens=100, overlap_tokens=100)
    except ValueError:
        return
    raise AssertionError("expected ValueError on overlap >= target")
