from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse


TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"ref", "ref_src", "fbclid", "gclid", "mc_cid", "mc_eid"}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def canonicalize_url(url: str, base_url: str | None = None) -> str:
    if not url:
        return ""
    if base_url:
        url = urljoin(base_url, url)
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key in TRACKING_PARAMS or any(key.startswith(prefix) for prefix in TRACKING_PREFIXES):
            continue
        query_items.append((key, value))
    query = urlencode(query_items, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def build_canonical_id(source_id: str, title: str, url: str, published_at: datetime | None) -> str:
    if url:
        raw = canonicalize_url(url)
    else:
        date_part = published_at.isoformat() if published_at else ""
        raw = f"{source_id}:{clean_text(title).lower()}:{date_part}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_datetime(value: object) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        text = value.strip()
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            for date_format in ("%d %b %Y", "%d %B %Y"):
                try:
                    dt = datetime.strptime(text, date_format)
                    break
                except ValueError:
                    dt = None
            if dt is None:
                try:
                    dt = parsedate_to_datetime(text)
                except (TypeError, ValueError):
                    return None
    else:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_path(data: object, path: str | None) -> object:
    if not path:
        return data
    current = data
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
