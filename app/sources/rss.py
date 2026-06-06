import feedparser
import httpx
from bs4 import BeautifulSoup

from app.models import NewsItem, SourceConfig
from app.utils import build_canonical_id, canonicalize_url, clean_text, parse_datetime


def _entry_content(entry) -> str:
    content_entries = entry.get("content") or []
    if content_entries:
        raw_content = content_entries[0].get("value", "")
    else:
        raw_content = entry.get("summary") or entry.get("description") or ""
    if "<" in raw_content and ">" in raw_content:
        raw_content = BeautifulSoup(raw_content, "html.parser").get_text("\n", strip=True)
    return clean_text(raw_content)


def fetch_rss(client: httpx.Client, source: SourceConfig, segment: str) -> list[NewsItem]:
    response = client.get(source.url)
    response.raise_for_status()
    parsed = feedparser.parse(response.text)
    items: list[NewsItem] = []
    for entry in parsed.entries:
        title = clean_text(entry.get("title"))
        url = canonicalize_url(entry.get("link", ""), source.url)
        summary = _entry_content(entry)
        published_at = parse_datetime(entry.get("published") or entry.get("updated"))
        if not title or not url:
            continue
        item = NewsItem(
            source_id=source.id,
            source_name=source.name,
            segment=segment,
            title=title,
            url=url,
            content_text=summary,
            published_at=published_at,
            metadata={"author": entry.get("author", "")},
        )
        item.canonical_id = build_canonical_id(source.id, item.title, item.url, item.published_at)
        items.append(item)
    return items
