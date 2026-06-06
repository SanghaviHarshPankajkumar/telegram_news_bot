from app.models import NewsItem, SourceConfig


SEGMENT_KEYWORDS_ANY = {
    "model_releases": [
        "released",
        "launches",
        "launched",
        "unveils",
        "introduced",
        "introduces",
        "now available",
        "open-weight",
        "open source model",
        "api preview",
    ],
    "tools": [
        "ai",
        "automation",
        "assistant",
        "generator",
        "summarizer",
        "platform",
        "app",
        "workspace",
        "agent",
    ],
    "big_tech": [
        "openai",
        "anthropic",
        "nvidia",
        "xai",
        "grok",
        "chatgpt",
        "claude",
        "gpu",
        "regulation",
        "policy",
    ],
    "agent_harness_engineering": [
        "agent",
        "agents",
        "langgraph",
        "langsmith",
        "evaluation",
        "eval",
        "memory",
        "context",
        "workflow",
        "tool",
        "harness",
        "coding agent",
    ],
    "agent_learning": [
        "agent",
        "agents",
        "langgraph",
        "langsmith",
        "evaluation",
        "eval",
        "memory",
        "context",
        "workflow",
        "tool",
        "harness",
        "coding agent",
    ],
}

SEGMENT_KEYWORDS_ALL = {
    "model_releases": [
        "model",
    ],
}


def matches_filters(item: NewsItem, source: SourceConfig) -> bool:
    filters = source.filters or {}
    haystack = f"{item.title} {item.content_text} {' '.join(map(str, item.metadata.values()))}".lower()

    any_terms = [term.lower() for term in filters.get("keywords_any", [])]
    if any_terms and not any(term in haystack for term in any_terms):
        return False

    all_terms = [term.lower() for term in filters.get("keywords_all", [])]
    if all_terms and not all(term in haystack for term in all_terms):
        return False

    excluded = [term.lower() for term in filters.get("exclude_keywords", [])]
    if excluded and any(term in haystack for term in excluded):
        return False

    return True


def matches_segment_defaults(item: NewsItem, segment: str) -> bool:
    haystack = f"{item.title} {item.content_text} {' '.join(map(str, item.metadata.values()))}".lower()
    if segment == "tools" and not _looks_like_real_tool(item, haystack):
        return False

    all_terms = [term.lower() for term in SEGMENT_KEYWORDS_ALL.get(segment, [])]
    if all_terms and not all(term in haystack for term in all_terms):
        return False

    any_terms = [term.lower() for term in SEGMENT_KEYWORDS_ANY.get(segment, [])]
    if any_terms and not any(term in haystack for term in any_terms):
        return False

    return True


def _looks_like_real_tool(item: NewsItem, haystack: str) -> bool:
    blocked_domains = [
        "zdnet.com",
        "arxiv.org",
        "theverge.com",
        "blogs.nvidia.com",
        "venturebeat.com",
        "huggingface.co/blog",
        "wsj.com",
        "techcrunch.com",
        "wired.com",
    ]
    if any(domain in item.url.lower() for domain in blocked_domains):
        return False
    blocked_title_terms = [
        "i compared",
        "researchers",
        "benchmark",
        "paper",
        "study",
        "report",
        "news",
        "says it can",
    ]
    if any(term in item.title.lower() for term in blocked_title_terms):
        return False
    tool_signals = [
        "pricing",
        "freemium",
        "free",
        "paid",
        "use cases",
        "platform",
        "app",
        "tool",
        "assistant",
        "generator",
        "summarizer",
        "workspace",
    ]
    return any(signal in haystack for signal in tool_signals)


def segment_score(item: NewsItem, segment: str) -> int:
    haystack = f"{item.title} {item.content_text} {' '.join(map(str, item.metadata.values()))}".lower()
    if segment not in {"agent_harness_engineering", "agent_learning"}:
        return 0
    weighted_terms = {
        "coding agent": 8,
        "agent harness": 8,
        "agent engineering": 8,
        "agents": 5,
        "agent": 5,
        "langgraph": 5,
        "langsmith": 4,
        "tool": 3,
        "workflow": 3,
        "eval": 3,
        "evaluation": 3,
        "memory": 3,
        "context": 3,
        "architecture": 1,
    }
    return sum(weight for term, weight in weighted_terms.items() if term in haystack)
