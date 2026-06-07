from datetime import datetime
from zoneinfo import ZoneInfo

from app.jobs import due_jobs


class NeverRunStore:
    def has_successful_job_run_since(self, job_name, since):
        return False


class AlreadyRunStore:
    def has_successful_job_run_since(self, job_name, since):
        return True


def test_due_jobs_at_daily_dose_time(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Asia/Kolkata")
    jobs = due_jobs(datetime(2026, 6, 6, 3, 30, tzinfo=ZoneInfo("UTC")))
    assert "daily_dose_ds" in jobs
    assert "model_releases" in jobs
    assert "prit_blog" in jobs


def test_due_jobs_at_agent_harness_time(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Asia/Kolkata")
    jobs = due_jobs(datetime(2026, 6, 6, 13, 30, tzinfo=ZoneInfo("UTC")))
    assert "agent_harness_engineering" in jobs
    assert "sebastian_blog" in jobs


def test_due_jobs_at_big_tech_noon_time(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Asia/Kolkata")
    jobs = due_jobs(datetime(2026, 6, 6, 6, 30, tzinfo=ZoneInfo("UTC")))
    assert "big_tech_noon" in jobs
    assert "tools" in jobs


def test_due_jobs_at_big_tech_evening_time(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Asia/Kolkata")
    jobs = due_jobs(datetime(2026, 6, 6, 14, 30, tzinfo=ZoneInfo("UTC")))
    assert "big_tech_evening" in jobs


def test_due_jobs_catches_up_late_scheduled_run(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Asia/Kolkata")
    jobs = due_jobs(datetime(2026, 6, 6, 4, 12, tzinfo=ZoneInfo("UTC")), NeverRunStore())
    assert "daily_dose_ds" in jobs


def test_due_jobs_does_not_repeat_completed_slot(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Asia/Kolkata")
    jobs = due_jobs(datetime(2026, 6, 6, 4, 12, tzinfo=ZoneInfo("UTC")), AlreadyRunStore())
    assert "daily_dose_ds" not in jobs


def test_due_jobs_does_not_catch_up_after_window(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Asia/Kolkata")
    jobs = due_jobs(datetime(2026, 6, 6, 7, 1, tzinfo=ZoneInfo("UTC")), NeverRunStore())
    assert "daily_dose_ds" not in jobs
