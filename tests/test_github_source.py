import httpx

from app.models import SourceConfig
from app.sources.github import fetch_github_search


class MockTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if str(request.url).endswith("/repos/org/repo/readme"):
            return httpx.Response(200, text="# Repo\nBuild autonomous AI agents.")
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "full_name": "org/repo",
                        "html_url": "https://github.com/org/repo",
                        "description": "An AI agent repo.",
                        "created_at": "2026-06-06T00:00:00Z",
                        "updated_at": "2026-06-06T01:00:00Z",
                        "stargazers_count": 100,
                        "forks_count": 10,
                        "open_issues_count": 2,
                        "language": "Python",
                    }
                ]
            },
        )


def test_fetch_github_search_includes_readme():
    source = SourceConfig(
        id="github",
        name="GitHub",
        type="github_search",
        url="https://api.github.com/search/repositories",
        segments=["github_repo"],
        github={"q_template": "topic:ai", "per_page": 1},
    )
    items = fetch_github_search(httpx.Client(transport=MockTransport()), source, "github_repo")
    assert "README" in items[0].content_text
    assert "Build autonomous AI agents" in items[0].content_text
    assert items[0].metadata["stars"] == 100
