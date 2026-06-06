from pathlib import Path

from app.source_loader import load_sources, sources_for_segment


def test_load_sources():
    sources = load_sources(Path("sources.yaml"))
    assert sources
    assert sources_for_segment(sources, "tools")

