from pathlib import Path

import yaml

from app.models import SourceConfig, SourceRegistry


def load_sources(path: Path) -> list[SourceConfig]:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return SourceRegistry.model_validate(raw).sources


def sources_for_segment(sources: list[SourceConfig], segment: str) -> list[SourceConfig]:
    return [source for source in sources if source.enabled and segment in source.segments]

