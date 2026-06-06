from collections.abc import Iterable

import httpx

from app.models import NewsItem, SourceConfig
from app.sources.github import fetch_github_search
from app.sources.html import fetch_html
from app.sources.json_feed import fetch_json
from app.sources.rss import fetch_rss
from app.sources.supabase_tools import fetch_supabase_tools


def fetch_source(
    client: httpx.Client,
    source: SourceConfig,
    segment: str,
    github_token: str = "",
) -> Iterable[NewsItem]:
    source_type = source.type.lower()
    if source_type in {"rss", "atom"}:
        return fetch_rss(client, source, segment)
    if source_type == "json":
        return fetch_json(client, source, segment)
    if source_type == "html":
        return fetch_html(client, source, segment)
    if source_type == "github_search":
        return fetch_github_search(client, source, segment, github_token)
    if source_type == "github_trending_html":
        return fetch_html(client, source, segment)
    if source_type == "supabase_tools":
        return fetch_supabase_tools(client, source, segment)
    raise ValueError(f"Unsupported source type: {source.type}")
