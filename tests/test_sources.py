import httpx

from app.models import SourceConfig
from app.sources.html import fetch_html
from app.sources.json_feed import fetch_json
from app.sources.rss import fetch_rss


class MockTransport(httpx.BaseTransport):
    def __init__(self, body: str, content_type: str = "text/plain"):
        self.body = body
        self.content_type = content_type

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=self.body, headers={"content-type": self.content_type})


def test_fetch_json_normalizes_items():
    source = SourceConfig(
        id="json",
        name="JSON",
        type="json",
        url="https://example.com/feed.json",
        segments=["tools"],
        json={
            "items_path": "items",
            "title_path": "title",
            "url_path": "url",
            "summary_path": "summary",
            "published_at_path": "published",
        },
    )
    client = httpx.Client(transport=MockTransport('{"items":[{"title":"Tool","url":"/tool","summary":"S","published":"2026-06-06T00:00:00Z"}]}', "application/json"))
    items = fetch_json(client, source, "tools")
    assert items[0].url == "https://example.com/tool"
    assert items[0].canonical_id


def test_fetch_html_extracts_links():
    source = SourceConfig(
        id="html",
        name="HTML",
        type="html",
        url="https://example.com",
        segments=["tools"],
        selectors={"item": "a[href]", "title": "", "link": "@self"},
    )
    client = httpx.Client(transport=MockTransport('<a href="/x">New AI Tool</a>', "text/html"))
    items = fetch_html(client, source, "tools")
    assert items[0].title == "New AI Tool"
    assert items[0].url == "https://example.com/x"


def test_fetch_rss_extracts_entries():
    source = SourceConfig(
        id="rss",
        name="RSS",
        type="rss",
        url="https://example.com/feed",
        segments=["big_tech"],
    )
    body = """<?xml version="1.0"?>
    <rss version="2.0"><channel><item><title>AI News</title><link>https://example.com/n</link><description>Summary</description><pubDate>Sat, 06 Jun 2026 00:00:00 GMT</pubDate></item></channel></rss>"""
    client = httpx.Client(transport=MockTransport(body, "application/rss+xml"))
    items = fetch_rss(client, source, "big_tech")
    assert items[0].title == "AI News"
    assert items[0].content_text == "Summary"


def test_fetch_rss_prefers_full_content_encoded():
    source = SourceConfig(
        id="rss",
        name="RSS",
        type="rss",
        url="https://example.com/feed",
        segments=["daily_dose_ds"],
    )
    body = """<?xml version="1.0"?>
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <item>
          <title>Newsletter</title>
          <link>https://example.com/newsletter</link>
          <description>Short summary</description>
          <content:encoded><![CDATA[<p>Full newsletter body with CopilotKit and Hermes.</p>]]></content:encoded>
        </item>
      </channel>
    </rss>"""
    client = httpx.Client(transport=MockTransport(body, "application/rss+xml"))
    items = fetch_rss(client, source, "daily_dose_ds")
    assert items[0].content_text == "Full newsletter body with CopilotKit and Hermes."
