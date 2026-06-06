from datetime import datetime, timezone

from app.jobs import fresh_cutoff_for_today, is_fresh_for_impromptu
from app.models import NewsItem


def test_fresh_cutoff_uses_ist_midnight():
    now = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
    cutoff = fresh_cutoff_for_today("Asia/Kolkata", now)
    assert cutoff == datetime(2026, 6, 5, 18, 30, tzinfo=timezone.utc)


def test_impromptu_rejects_old_published_item():
    item = NewsItem(
        source_id="prit",
        source_name="Prit",
        segment="prit_blog",
        title="Old post",
        url="https://example.com",
        published_at=datetime(2026, 2, 20, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
    assert not is_fresh_for_impromptu("prit_blog", item, "Asia/Kolkata", now)


def test_impromptu_accepts_today_item():
    item = NewsItem(
        source_id="sebastian",
        source_name="Sebastian",
        segment="sebastian_blog",
        title="Today post",
        url="https://example.com",
        published_at=datetime(2026, 6, 6, 11, 16, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
    assert is_fresh_for_impromptu("sebastian_blog", item, "Asia/Kolkata", now)


def test_impromptu_rejects_missing_date():
    item = NewsItem(
        source_id="model",
        source_name="Model Source",
        segment="model_releases",
        title="Undated model release",
        url="https://example.com",
    )
    assert not is_fresh_for_impromptu("model_releases", item, "Asia/Kolkata")
