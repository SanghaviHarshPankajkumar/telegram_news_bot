from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    id: str
    name: str
    type: str
    url: str
    enabled: bool = True
    segments: list[str] = Field(default_factory=list)
    selectors: dict[str, str] = Field(default_factory=dict)
    filters: dict[str, list[str]] = Field(default_factory=dict)
    json_config: dict[str, str] = Field(default_factory=dict, alias="json")
    github: dict[str, Any] = Field(default_factory=dict)
    supabase: dict[str, Any] = Field(default_factory=dict)


class SourceRegistry(BaseModel):
    sources: list[SourceConfig]


class NewsItem(BaseModel):
    source_id: str
    source_name: str
    segment: str | None = None
    title: str
    url: str
    content_text: str = ""
    published_at: datetime | None = None
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    canonical_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
