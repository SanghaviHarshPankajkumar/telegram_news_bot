import httpx

from app.models import SourceConfig
from app.sources.supabase_tools import fetch_supabase_tools


class MockTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "name": "PodPulse AI",
                    "slug": "podpulse-ai",
                    "short_description": "AI podcast summarizer.",
                    "website_url": "https://podpulse.ai/",
                    "pricing": "freemium",
                    "is_just_landed": True,
                    "is_verified": False,
                    "created_at": "2026-03-03T08:56:51Z",
                    "use_cases": ["Podcast research"],
                }
            ],
        )


def test_fetch_supabase_tools():
    source = SourceConfig(
        id="nextool",
        name="Nextool",
        type="supabase_tools",
        url="https://example.supabase.co/rest/v1/tools",
        segments=["tools"],
        supabase={"anon_key": "key"},
    )
    items = fetch_supabase_tools(httpx.Client(transport=MockTransport()), source, "tools")
    assert items[0].title == "PodPulse AI"
    assert items[0].url == "https://podpulse.ai/"
    assert items[0].metadata["pricing"] == "freemium"
