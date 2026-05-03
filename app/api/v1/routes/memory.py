from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import get_memory

router = APIRouter()


@router.get("/decisions")
def decisions(limit: int = Query(20, ge=1, le=500)) -> dict:
    rows = get_memory().read_recent("decisions", limit)
    return {"count": len(rows), "items": rows}


@router.get("/outcomes")
def outcomes(limit: int = Query(20, ge=1, le=500)) -> dict:
    rows = get_memory().read_recent("outcomes", limit)
    return {"count": len(rows), "items": rows}


@router.get("/lessons")
def lessons() -> dict:
    rows = get_memory().read_all("lessons")
    return {"count": len(rows), "items": rows}
