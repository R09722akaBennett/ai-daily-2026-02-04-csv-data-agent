"""Demo endpoint — returns the pre-baked extraction so prospects can see the
shape of the output without any installation."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_settings
from app.core import chunker as chunker_mod
from app.core import exports, quality
from app.core.config import Settings
from app.services.demo_fixture import build_demo_document

router = APIRouter()


@router.get("/demo")
def demo(settings: Settings = Depends(get_settings)) -> dict:
    doc = build_demo_document()
    doc.warnings = quality.assess(doc)
    payload = exports.to_full_json(doc)
    chunks = chunker_mod.chunk_document(
        doc,
        target_tokens=settings.chunk_target_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    payload["rag_chunks"] = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text,
            "heading_path": c.heading_path,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "token_estimate": c.token_estimate,
        }
        for c in chunks
    ]
    return payload
