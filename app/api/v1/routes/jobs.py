from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_jobs
from app.core import exports
from app.services.jobs import JobStore

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job(job_id: str, jobs: JobStore = Depends(get_jobs)) -> dict:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    payload: dict = {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
        "error": job.error,
    }
    if job.result is not None:
        payload["result"] = exports.to_full_json(job.result)
    return payload


@router.get("/jobs")
def list_jobs(limit: int = 20, jobs: JobStore = Depends(get_jobs)) -> dict:
    items = jobs.list_recent(limit=limit)
    return {
        "count": len(items),
        "items": [
            {
                "job_id": j.id,
                "filename": j.filename,
                "status": j.status,
                "created_at": j.created_at,
                "finished_at": j.finished_at,
            }
            for j in items
        ],
    }
