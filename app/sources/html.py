import re

from bs4 import BeautifulSoup
import httpx

from app.models import NewsItem, SourceConfig
from app.utils import build_canonical_id, canonicalize_url, clean_text, parse_datetime


def _extract_text(element, selector: str) -> str:
    if not selector:
        return clean_text(element.get_text(" ", strip=True))
    found = element.select_one(selector)
    return clean_text(found.get_text(" ", strip=True) if found else "")


def _extract_link(element, selector: str, base_url: str) -> str:
    if selector == "@self":
        href = element.get("href", "")
    elif selector:
        found = element.select_one(selector)
        href = found.get("href", "") if found else ""
    else:
        found = element if element.name == "a" else element.select_one("a[href]")
        href = found.get("href", "") if found else ""
    return canonicalize_url(href, base_url)


def fetch_html(client: httpx.Client, source: SourceConfig, segment: str) -> list[NewsItem]:
    response = client.get(source.url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    selectors = source.selectors or {}
    item_selector = selectors.get("item") or "article"
    title_selector = selectors.get("title", "")
    link_selector = selectors.get("link", "")
    summary_selector = selectors.get("summary", "")
    published_selector = selectors.get("published_at", "")

    items: list[NewsItem] = []
    seen_urls: set[str] = set()
    for element in soup.select(item_selector):
        title = _extract_text(element, title_selector)
        url = _extract_link(element, link_selector, source.url)
        summary = _extract_text(element, summary_selector) if summary_selector else ""
        published_text = _extract_text(element, published_selector) if published_selector else ""
        published_at = parse_datetime(published_text)
        if not published_at:
            date_match = re.search(r"\b(\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4})\b", title)
            if date_match:
                published_at = parse_datetime(date_match.group(1))
        if not title or not url or url in seen_urls:
            continue
        if title.lower() in {"home", "blog", "about", "subscribe", "tools", "ai news"}:
            continue
        seen_urls.add(url)
        item = NewsItem(
            source_id=source.id,
            source_name=source.name,
            segment=segment,
            title=title,
            url=url,
            content_text=summary,
            published_at=published_at,
        )
        item.canonical_id = build_canonical_id(source.id, item.title, item.url, item.published_at)
        items.append(item)
    return items
