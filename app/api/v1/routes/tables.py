from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from app.api.deps import get_jobs
from app.core import exports
from app.services.jobs import JobStore

router = APIRouter()


@router.get("/jobs/{job_id}/tables/{index}.csv", response_class=PlainTextResponse)
def get_table_csv(job_id: str, index: int, jobs: JobStore = Depends(get_jobs)) -> PlainTextResponse:
    job = jobs.get(job_id)
    if not job or job.result is None:
        raise HTTPException(status_code=404, detail="job not found or not finished")
    tables = job.result.tables
    if index < 0 or index >= len(tables):
        raise HTTPException(status_code=404, detail=f"table index {index} out of range")
    csv_text = exports.table_to_csv(tables[index].rows)
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=table-{index:02d}-p{tables[index].page or 0:03d}.csv"
            )
        },
    )
