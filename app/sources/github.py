from datetime import datetime, timedelta, timezone

import httpx

from app.models import NewsItem, SourceConfig
from app.utils import build_canonical_id, canonicalize_url, clean_text, parse_datetime


def _github_headers(github_token: str = "") -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def _fetch_readme(client: httpx.Client, full_name: str, github_token: str = "") -> str:
    response = client.get(
        f"https://api.github.com/repos/{full_name}/readme",
        headers={**_github_headers(github_token), "Accept": "application/vnd.github.raw"},
    )
    if response.status_code == 404:
        return ""
    response.raise_for_status()
    return clean_text(response.text[:10000])


def fetch_github_search(
    client: httpx.Client,
    source: SourceConfig,
    segment: str,
    github_token: str = "",
) -> list[NewsItem]:
    config = source.github
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    query = (config.get("q_template") or "topic:artificial-intelligence").format(date_7d=seven_days_ago)
    params = {
        "q": query,
        "sort": config.get("sort", "stars"),
        "order": config.get("order", "desc"),
        "per_page": int(config.get("per_page", 10)),
    }
    headers = _github_headers(github_token)

    response = client.get(source.url, params=params, headers=headers)
    response.raise_for_status()
    payload = response.json()
    items: list[NewsItem] = []
    for repo in payload.get("items", []):
        title = clean_text(repo.get("full_name", ""))
        url = canonicalize_url(repo.get("html_url", ""), source.url)
        description = clean_text(repo.get("description", ""))
        readme = _fetch_readme(client, title, github_token) if title else ""
        content = description
        if readme:
            content = clean_text(f"{description}\n\nREADME:\n{readme}")
        published_at = parse_datetime(repo.get("created_at"))
        if not title or not url:
            continue
        item = NewsItem(
            source_id=source.id,
            source_name=source.name,
            segment=segment,
            title=title,
            url=url,
            content_text=content,
            published_at=published_at,
            metadata={
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language", ""),
                "updated_at": repo.get("updated_at", ""),
                "forks": repo.get("forks_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
            },
        )
        item.canonical_id = build_canonical_id(source.id, item.title, item.url, item.published_at)
        items.append(item)
    return items
