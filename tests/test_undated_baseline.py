from datetime import datetime, timezone

from app.jobs import handle_undated_item
from app.models import NewsItem


class BaselineStore:
    def __init__(self, initialized=False):
        self.initialized = initialized
        self.baselined = []
        self.inserted = []

    def is_source_initialized(self, source_id, segment):
        return self.initialized

    def mark_item_seen_without_sending(self, item, reason):
        self.baselined.append((item.canonical_id, reason))

    def insert_item_if_new(self, item):
        self.inserted.append(item.canonical_id)
        return True


def item():
    return NewsItem(
        source_id="undated",
        source_name="Undated",
        segment="prit_blog",
        title="New post",
        url="https://example.com/new-post",
        first_seen_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
        canonical_id="abc",
    )


def test_undated_item_is_baselined_before_source_is_initialized():
    store = BaselineStore(initialized=False)

    should_send = handle_undated_item("undated", "prit_blog", item(), store, dry_run=False)

    assert not should_send
    assert store.baselined == [("abc", "baseline_undated_source")]
    assert store.inserted == []


def test_undated_item_can_send_after_source_is_initialized():
    store = BaselineStore(initialized=True)

    should_send = handle_undated_item("undated", "prit_blog", item(), store, dry_run=False)

    assert should_send
    assert store.baselined == []
    assert store.inserted == ["abc"]


def test_undated_item_does_not_send_in_dry_run():
    store = BaselineStore(initialized=True)

    should_send = handle_undated_item("undated", "prit_blog", item(), store, dry_run=True)

    assert not should_send
    assert store.baselined == []
    assert store.inserted == []
