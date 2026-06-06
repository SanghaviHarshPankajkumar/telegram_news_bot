import httpx

from app.models import NewsItem, SourceConfig
from app.utils import build_canonical_id, canonicalize_url, clean_text, parse_datetime


def fetch_supabase_tools(client: httpx.Client, source: SourceConfig, segment: str) -> list[NewsItem]:
    config = source.supabase
    anon_key = config.get("anon_key", "")
    if not anon_key:
        raise ValueError(f"supabase_tools source {source.id} needs supabase.anon_key")

    params = {
        "select": config.get(
            "select",
            "id,name,slug,short_description,tagline,website_url,pricing,is_just_landed,is_verified,created_at,use_cases",
        ),
        "order": config.get("order", "created_at.desc"),
        "limit": str(config.get("limit", 20)),
    }
    for key, value in config.get("filters", {}).items():
        params[key] = value

    response = client.get(
        source.url,
        params=params,
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Accept": "application/json",
        },
    )
    response.raise_for_status()

    items: list[NewsItem] = []
    for raw in response.json():
        title = clean_text(raw.get("name", ""))
        website_url = canonicalize_url(raw.get("website_url", ""))
        slug = clean_text(raw.get("slug", ""))
        directory_url = canonicalize_url(f"https://nextool.ai/tool/{slug}") if slug else website_url
        description = clean_text(raw.get("short_description") or raw.get("tagline") or raw.get("description"))
        use_cases = raw.get("use_cases") or []
        if use_cases:
            description = clean_text(description + " Use cases: " + "; ".join(use_cases[:4]))
        published_at = parse_datetime(raw.get("created_at"))
        if not title or not website_url:
            continue
        item = NewsItem(
            source_id=source.id,
            source_name=source.name,
            segment=segment,
            title=title,
            url=website_url,
            content_text=description,
            published_at=published_at,
            metadata={
                "directory_url": directory_url,
                "pricing": raw.get("pricing", ""),
                "is_verified": raw.get("is_verified", False),
                "is_just_landed": raw.get("is_just_landed", False),
            },
        )
        item.canonical_id = build_canonical_id(source.id, item.title, item.url, item.published_at)
        items.append(item)
    return items
