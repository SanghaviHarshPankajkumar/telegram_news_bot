import httpx

from app.models import NewsItem, SourceConfig
from app.utils import build_canonical_id, canonicalize_url, clean_text, get_path, parse_datetime


def fetch_json(client: httpx.Client, source: SourceConfig, segment: str) -> list[NewsItem]:
    response = client.get(source.url)
    response.raise_for_status()
    data = response.json()
    config = source.json_config
    raw_items = get_path(data, config.get("items_path")) or []
    if not isinstance(raw_items, list):
        return []

    items: list[NewsItem] = []
    for raw in raw_items:
        title = clean_text(str(get_path(raw, config.get("title_path")) or ""))
        url = canonicalize_url(str(get_path(raw, config.get("url_path")) or ""), source.url)
        summary = clean_text(str(get_path(raw, config.get("summary_path")) or ""))
        published_at = parse_datetime(get_path(raw, config.get("published_at_path")))
        tags = get_path(raw, config.get("tags_path")) if config.get("tags_path") else []
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
            metadata={"tags": tags or []},
        )
        item.canonical_id = build_canonical_id(source.id, item.title, item.url, item.published_at)
        items.append(item)
    return items
