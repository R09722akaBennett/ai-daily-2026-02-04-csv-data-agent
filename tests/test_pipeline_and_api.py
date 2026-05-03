"""Pipeline + API tests.

Docling is intentionally NOT installed in CI: we exercise the demo-mode path so
the public API contract is verified without dragging in 5GB of models.
"""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import build_app
from app.services import pipeline


def test_demo_mode_returns_fixture_when_docling_missing() -> None:
    settings = Settings(demo_mode=True)
    doc = pipeline.extract_bytes(settings=settings, data=b"%PDF-fake", filename="hello.pdf")
    assert doc.source_name == "hello.pdf"
    assert doc.tables, "demo fixture must have at least one table"
    assert any(s.heading == "EU" for s in doc.sections)


def test_pipeline_raises_when_demo_disabled_and_docling_missing() -> None:
    settings = Settings(demo_mode=False)
    try:
        pipeline.extract_bytes(settings=settings, data=b"%PDF-fake", filename="x.pdf")
    except pipeline.ExtractionUnavailable:
        return
    raise AssertionError("expected ExtractionUnavailable")


def test_health_endpoint() -> None:
    client = TestClient(build_app())
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_demo_endpoint_payload_shape() -> None:
    client = TestClient(build_app())
    r = client.get("/api/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["source_name"].endswith(".pdf")
    assert body["page_count"] == 4
    assert len(body["tables"]) == 1
    assert body["rag_chunks"], "demo must include RAG chunks"
    chunk = body["rag_chunks"][0]
    assert "heading_path" in chunk and "page_start" in chunk


def test_extract_endpoint_uses_demo_mode_when_docling_missing(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "true")
    # Force settings cache reset so the env var is read.
    from app.api import deps

    deps.get_settings.cache_clear()
    client = TestClient(build_app())
    r = client.post(
        "/api/extract",
        files={"file": ("hello.pdf", b"%PDF-fake bytes", "application/pdf")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source_name"] == "hello.pdf"
    assert body["tables"]


def test_extract_rejects_empty_upload(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "true")
    from app.api import deps

    deps.get_settings.cache_clear()
    client = TestClient(build_app())
    r = client.post("/api/extract", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert r.status_code == 400


def test_jobs_404_when_unknown() -> None:
    client = TestClient(build_app())
    r = client.get("/api/jobs/does-not-exist")
    assert r.status_code == 404


def test_table_csv_download(monkeypatch) -> None:
    """Submit a job, wait for it to finish (BackgroundTasks runs synchronously in TestClient),
    then pull a table as CSV."""
    monkeypatch.setenv("DEMO_MODE", "true")
    from app.api import deps

    deps.get_settings.cache_clear()
    client = TestClient(build_app())
    submit = client.post(
        "/api/jobs",
        files={"file": ("hello.pdf", b"%PDF-fake bytes", "application/pdf")},
    )
    assert submit.status_code == 200
    job_id = submit.json()["job_id"]
    # BackgroundTasks fires after the response is sent — but TestClient blocks on it.
    status = client.get(f"/api/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "done"
    csv_resp = client.get(f"/api/jobs/{job_id}/tables/0.csv")
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert "Region,Vendors" in csv_resp.text
