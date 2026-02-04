from fastapi.testclient import TestClient

from app.main import build_app


def test_health_ok() -> None:
    client = TestClient(build_app())
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
