from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile

from app.api.deps import get_jobs, get_settings
from app.core import chunker as chunker_mod
from app.core import exports
from app.core.config import Settings
from app.services import pipeline
from app.services.jobs import JobStore

router = APIRouter()


@router.post("/extract")
def extract_sync(
    file: UploadFile = File(...),
    rag: bool = Query(True, description="Include RAG-ready chunks in the response."),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Synchronous extraction. Suitable for files that finish in <60s."""
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds MAX_UPLOAD_MB={settings.max_upload_mb}.",
        )
    try:
        doc = pipeline.extract_bytes(
            settings=settings, data=data, filename=file.filename or "upload.bin"
        )
    except pipeline.ExtractionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"extraction failed: {exc}") from exc

    payload = exports.to_full_json(doc)
    if rag:
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


def _run_job(
    job_id: str, *, settings: Settings, data: bytes, filename: str, jobs: JobStore
) -> None:
    jobs.update(job_id, status="running")
    try:
        doc = pipeline.extract_bytes(settings=settings, data=data, filename=filename)
        jobs.update(job_id, status="done", result=doc)
    except Exception as exc:  # noqa: BLE001 — capture for the API consumer
        jobs.update(job_id, status="error", error=f"{type(exc).__name__}: {exc}")


@router.post("/jobs")
def submit_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    jobs: JobStore = Depends(get_jobs),
) -> dict:
    """Async extraction. Returns ``{job_id}``; poll ``/jobs/{id}``."""
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds MAX_UPLOAD_MB={settings.max_upload_mb}.",
        )
    job = jobs.submit(filename=file.filename or "upload.bin")
    background_tasks.add_task(
        _run_job,
        job.id,
        settings=settings,
        data=data,
        filename=job.filename,
        jobs=jobs,
    )
    return {"job_id": job.id, "status": job.status, "filename": job.filename}
