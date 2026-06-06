from datetime import datetime, timezone

from app.utils import build_canonical_id, canonicalize_url, get_path, parse_datetime


def test_canonicalize_url_removes_tracking_params():
    url = canonicalize_url("https://Example.com/path/?utm_source=x&a=1#frag")
    assert url == "https://example.com/path?a=1"


def test_build_canonical_id_prefers_url():
    first = build_canonical_id("a", "Title", "https://example.com/?utm_campaign=x", None)
    second = build_canonical_id("b", "Other", "https://example.com/", datetime.now(timezone.utc))
    assert first == second


def test_parse_datetime_iso_z():
    parsed = parse_datetime("2026-06-06T12:00:00Z")
    assert parsed == datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)


def test_parse_datetime_short_date():
    parsed = parse_datetime("20 Feb 2026")
    assert parsed == datetime(2026, 2, 20, tzinfo=timezone.utc)


def test_get_path_reads_nested_dict_and_list():
    data = {"items": [{"title": "Hello"}]}
    assert get_path(data, "items.0.title") == "Hello"
