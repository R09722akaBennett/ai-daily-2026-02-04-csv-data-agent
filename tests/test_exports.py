import csv
import io
import json

from app.core import exports
from app.core.types import ExtractedDocument, ExtractedSection, ExtractedTable, RagChunk


def _doc() -> ExtractedDocument:
    return ExtractedDocument(
        source_name="x.pdf",
        markdown="# H\n\nbody",
        sections=[
            ExtractedSection(
                heading="H", level=1, heading_path=["H"], text="body", page_start=1, page_end=1
            )
        ],
        tables=[ExtractedTable(index=0, page=2, rows=[["a", "b"], ["1", "2"]], caption="cap")],
        page_count=2,
    )


def test_to_full_json_round_trips() -> None:
    payload = exports.to_full_json(_doc())
    raw = json.dumps(payload)  # must be JSON-serializable
    parsed = json.loads(raw)
    assert parsed["source_name"] == "x.pdf"
    assert parsed["tables"][0]["rows"] == [["a", "b"], ["1", "2"]]
    assert parsed["tables"][0]["caption"] == "cap"
    assert parsed["page_count"] == 2


def test_table_to_csv_quoting() -> None:
    rows = [["Name", "Note"], ["Alice", "with, comma"], ["Bob", 'with "quote"']]
    text = exports.table_to_csv(rows)
    parsed = list(csv.reader(io.StringIO(text)))
    assert parsed == rows


def test_to_table_csvs_keys_are_safe() -> None:
    out = exports.to_table_csvs(_doc())
    assert list(out.keys()) == ["table-00-p002.csv"]
    assert "a,b" in out["table-00-p002.csv"]


def test_to_rag_jsonl_is_one_object_per_line() -> None:
    chunks = [
        RagChunk(
            chunk_id="c1",
            text="hello",
            heading_path=["Doc", "Intro"],
            page_start=1,
            page_end=1,
            token_estimate=3,
            source_name="x.pdf",
        ),
        RagChunk(
            chunk_id="c2",
            text="world",
            heading_path=["Doc", "Intro"],
            page_start=1,
            page_end=2,
            token_estimate=3,
            source_name="x.pdf",
        ),
    ]
    text = exports.to_rag_jsonl(chunks)
    lines = [line for line in text.splitlines() if line.strip()]
    assert len(lines) == 2
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["chunk_id"] == "c1"
    assert parsed[0]["metadata"]["heading_path"] == ["Doc", "Intro"]
    assert parsed[1]["metadata"]["page_end"] == 2
