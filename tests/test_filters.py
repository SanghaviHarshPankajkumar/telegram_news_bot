from app.filters import matches_segment_defaults
from app.models import NewsItem


def test_model_release_filter_rejects_non_release_model_news():
    item = NewsItem(
        source_id="x",
        source_name="X",
        segment="model_releases",
        title="Meta keeps delaying the release of its new AI model",
        url="https://example.com",
    )
    assert not matches_segment_defaults(item, "model_releases")


def test_model_release_filter_accepts_launch():
    item = NewsItem(
        source_id="x",
        source_name="X",
        segment="model_releases",
        title="Google launches new Gemma model",
        url="https://example.com",
    )
    assert matches_segment_defaults(item, "model_releases")


def test_tools_filter_rejects_articles():
    item = NewsItem(
        source_id="x",
        source_name="X",
        segment="tools",
        title="I compared ChatGPT and Gemini's AI image generation",
        url="https://www.zdnet.com/article/beginner-ai-image-prompt-tip-chatgpt-gemini",
    )
    assert not matches_segment_defaults(item, "tools")


def test_tools_filter_accepts_actual_tool():
    item = NewsItem(
        source_id="nextool",
        source_name="Nextool",
        segment="tools",
        title="PodPulse AI",
        url="https://podpulse.ai/",
        content_text="AI podcast summarizer and discovery tool. Pricing: freemium. Use cases: podcast research.",
    )
    assert matches_segment_defaults(item, "tools")
