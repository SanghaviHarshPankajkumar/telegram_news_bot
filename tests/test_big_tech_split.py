from datetime import datetime, timezone

from app.jobs import chunk_items, select_big_tech_items
from app.models import NewsItem


def _item(index: int) -> NewsItem:
    return NewsItem(
        source_id="source",
        source_name="Source",
        segment="big_tech",
        title=f"Item {index}",
        url=f"https://example.com/{index}",
        published_at=datetime(2026, 6, index, tzinfo=timezone.utc),
    )


def test_big_tech_noon_selects_first_half_rounded_up():
    items = [_item(index) for index in range(1, 6)]
    selected = select_big_tech_items("big_tech_noon", items)
    assert [item.title for item in selected] == ["Item 5", "Item 4", "Item 3"]


def test_big_tech_evening_selects_all_remaining_candidates():
    items = [_item(index) for index in range(1, 3)]
    selected = select_big_tech_items("big_tech_evening", items)
    assert [item.title for item in selected] == ["Item 2", "Item 1"]


def test_chunk_items_splits_large_digest_into_messages():
    items = [_item(index) for index in range(1, 26)]
    chunks = chunk_items(items, 10)
    assert [len(chunk) for chunk in chunks] == [10, 10, 5]
