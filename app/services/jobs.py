"""In-memory job store for async extraction.

This is intentionally minimal: the daily project's job is to demonstrate the
pattern, not to be a production queue. For real deployments swap to Redis /
Celery / Cloud Tasks — the public surface (``submit / get / status``) won't change.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from app.core.types import ExtractedDocument

JobStatus = Literal["queued", "running", "done", "error"]


@dataclass
class Job:
    id: str
    filename: str
    status: JobStatus = "queued"
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    result: ExtractedDocument | None = None
    error: str | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit(self, filename: str) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], filename=filename)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        result: ExtractedDocument | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if status is not None:
                job.status = status
                if status in ("done", "error"):
                    job.finished_at = time.time()
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error

    def list_recent(self, limit: int = 20) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)[:limit]


_default_store: JobStore | None = None


def default_store() -> JobStore:
    global _default_store
    if _default_store is None:
        _default_store = JobStore()
    return _default_store
