"""Heading-aware RAG chunker.

Two reasons we don't just dump fixed-size chunks:
 1. RAG retrieval gets sharper when each chunk carries its heading_path —
    "Section 4.2 > Refund policy" is a useful hint for both the embedder
    and the LLM at answer time.
 2. Citations need page numbers. Docling already gives us page_start /
    page_end per section; we propagate that into the chunk so the answer
    UI can render "see page 14" without a second lookup.

Token estimate is a coarse `len(text) // 4` heuristic — good enough to size
chunks for most embedding models without dragging in a tokenizer dep.
"""

from __future__ import annotations

import re
import uuid

from app.core.types import ExtractedDocument, ExtractedSection, RagChunk

_SENT_SPLIT = re.compile(r"(?<=[.!?。！？])\s+|\n{2,}")


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _split_into_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
    return parts or [text.strip()]


def _pack(
    sentences: list[str],
    target_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Pack sentences into chunks ~target_tokens long, with sentence-level overlap."""
    chunks: list[str] = []
    buf: list[str] = []
    buf_tokens = 0
    for sent in sentences:
        t = _estimate_tokens(sent)
        if buf and buf_tokens + t > target_tokens:
            chunks.append(" ".join(buf).strip())
            # Build overlap tail from the end of the previous chunk.
            tail: list[str] = []
            tail_tokens = 0
            for s in reversed(buf):
                if tail_tokens + _estimate_tokens(s) > overlap_tokens:
                    break
                tail.insert(0, s)
                tail_tokens += _estimate_tokens(s)
            buf = list(tail)
            buf_tokens = tail_tokens
        buf.append(sent)
        buf_tokens += t
    if buf:
        chunks.append(" ".join(buf).strip())
    return chunks


def chunk_section(
    section: ExtractedSection,
    *,
    target_tokens: int,
    overlap_tokens: int,
    source_name: str,
) -> list[RagChunk]:
    sentences = _split_into_sentences(section.text)
    raw_chunks = _pack(sentences, target_tokens=target_tokens, overlap_tokens=overlap_tokens)
    return [
        RagChunk(
            chunk_id=uuid.uuid4().hex[:12],
            text=text,
            heading_path=list(section.heading_path),
            page_start=section.page_start,
            page_end=section.page_end,
            token_estimate=_estimate_tokens(text),
            source_name=source_name,
        )
        for text in raw_chunks
        if text
    ]


def chunk_document(
    doc: ExtractedDocument,
    *,
    target_tokens: int = 500,
    overlap_tokens: int = 60,
) -> list[RagChunk]:
    if target_tokens < 50:
        raise ValueError("target_tokens must be at least 50")
    if overlap_tokens < 0 or overlap_tokens >= target_tokens:
        raise ValueError("overlap_tokens must be in [0, target_tokens)")
    out: list[RagChunk] = []
    for section in doc.sections:
        out.extend(
            chunk_section(
                section,
                target_tokens=target_tokens,
                overlap_tokens=overlap_tokens,
                source_name=doc.source_name,
            )
        )
    return out
