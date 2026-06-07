from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_run_scheduled_endpoint_requires_secret(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("JOB_SECRET", "correct-secret")
    client = TestClient(app)

    response = client.post("/jobs/run-scheduled?secret=wrong-secret")

    assert response.status_code == 404


def test_run_scheduled_endpoint_runs_scheduler(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("JOB_SECRET", "correct-secret")
    called = {}

    def fake_run_scheduled(dry_run=False):
        called["dry_run"] = dry_run
        return 0

    monkeypatch.setattr("app.main.run_scheduled", fake_run_scheduled)
    client = TestClient(app)

    response = client.post("/jobs/run-scheduled?secret=correct-secret")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "exit_code": 0}
    assert called == {"dry_run": False}
