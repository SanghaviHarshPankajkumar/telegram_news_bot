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


def test_daily_dose_rejects_previous_ist_day():
    item = NewsItem(
        source_id="daily_dose_ds_feed",
        source_name="Daily Dose",
        segment="daily_dose_ds",
        title="Yesterday newsletter",
        url="https://example.com/yesterday",
        published_at=datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 7, 4, 0, tzinfo=timezone.utc)
    assert not is_fresh_for_impromptu("daily_dose_ds", item, "Asia/Kolkata", now)


def test_daily_dose_accepts_today_in_ist_even_if_utc_date_is_previous_day():
    item = NewsItem(
        source_id="daily_dose_ds_feed",
        source_name="Daily Dose",
        segment="daily_dose_ds",
        title="Today newsletter",
        url="https://example.com/today",
        published_at=datetime(2026, 6, 6, 20, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 7, 4, 0, tzinfo=timezone.utc)
    assert is_fresh_for_impromptu("daily_dose_ds", item, "Asia/Kolkata", now)


def test_tools_rejects_old_listing():
    item = NewsItem(
        source_id="nextool_just_landed",
        source_name="Nextool",
        segment="tools",
        title="Old tool",
        url="https://example.com/tool",
        published_at=datetime(2024, 6, 7, 6, 30, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 7, 7, 0, tzinfo=timezone.utc)
    assert not is_fresh_for_impromptu("tools", item, "Asia/Kolkata", now)


def test_tools_accepts_today_listing():
    item = NewsItem(
        source_id="nextool_just_landed",
        source_name="Nextool",
        segment="tools",
        title="Today tool",
        url="https://example.com/tool",
        published_at=datetime(2026, 6, 7, 6, 30, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 7, 7, 0, tzinfo=timezone.utc)
    assert is_fresh_for_impromptu("tools", item, "Asia/Kolkata", now)


def test_big_tech_rejects_previous_day_news():
    item = NewsItem(
        source_id="tensorfeed",
        source_name="TensorFeed",
        segment="big_tech",
        title="Old OpenAI news",
        url="https://example.com/news",
        published_at=datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 7, 7, 0, tzinfo=timezone.utc)
    assert not is_fresh_for_impromptu("big_tech", item, "Asia/Kolkata", now)


def test_github_repo_rejects_old_repo_update():
    item = NewsItem(
        source_id="github_search_ai",
        source_name="GitHub",
        segment="github_repo",
        title="Old repo",
        url="https://github.com/example/repo",
        published_at=datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 7, 7, 0, tzinfo=timezone.utc)
    assert not is_fresh_for_impromptu("github_repo", item, "Asia/Kolkata", now)


def test_agent_learning_rejects_old_fallback():
    item = NewsItem(
        source_id="langchain_blog",
        source_name="LangChain",
        segment="agent_learning",
        title="Old agent post",
        url="https://example.com/agent",
        published_at=datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc),
    )
    now = datetime(2026, 6, 7, 7, 0, tzinfo=timezone.utc)
    assert not is_fresh_for_impromptu("agent_learning", item, "Asia/Kolkata", now)
