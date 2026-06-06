from datetime import datetime

from langchain_openai import ChatOpenAI
from zoneinfo import ZoneInfo

from app.config import Settings
from app.models import NewsItem
from app.prompts import PromptBook


class Summarizer:
    def __init__(self, api_key: str, base_url: str, model: str, prompts: PromptBook, settings: Settings):
        if not api_key:
            raise ValueError("LIGHTNING_API_KEY is required")
        self.prompts = prompts
        self.settings = settings
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.2,
        )

    def _callbacks(self):
        if not self.settings.langfuse_enabled:
            return []
        if not self.settings.langfuse_public_key or not self.settings.langfuse_secret_key:
            return []
        try:
            from langfuse.langchain import CallbackHandler

            return [CallbackHandler()]
        except Exception as exc:
            print(f"langfuse_callback_disabled error={exc}")
            return []

    def summarize(
        self,
        segment: str,
        items: list[NewsItem],
        part_index: int = 1,
        part_total: int = 1,
    ) -> str:
        item_text = "\n\n".join(
            [
                f"Title: {item.title}\nURL: {item.url}\nSource: {item.source_name}\nPublished: {item.published_at}\nContent: {item.content_text}\nMetadata: {item.metadata}"
                for item in items
            ]
        )
        first = items[0]
        template = self.prompts.prompt_for(segment)
        digest_time_ist = datetime.now(ZoneInfo(self.settings.timezone)).strftime("%d %b %Y, %I:%M %p IST")
        published_at_ist = digest_time_ist
        if first.published_at:
            published_at_ist = first.published_at.astimezone(ZoneInfo(self.settings.timezone)).strftime("%d %b %Y, %I:%M %p IST")
        user_prompt = template.format(
            title=first.title,
            url=first.url,
            published_at_ist=published_at_ist,
            digest_time_ist=digest_time_ist,
            item_count=len(items),
            part_index=part_index,
            part_total=part_total,
        ) + "\n\nSource items:\n" + item_text
        response = self.llm.invoke(
            [
                ("system", self.prompts.system_prompt()),
                ("user", user_prompt),
            ],
            config={
                "callbacks": self._callbacks(),
                "metadata": {
                    "langfuse_session_id": segment,
                    "segment": segment,
                    "source_ids": [item.source_id for item in items],
                    "canonical_ids": [item.canonical_id for item in items],
                },
                "run_name": f"ai-news-bot-{segment}",
            },
        )
        return str(response.content).strip()


class DryRunSummarizer:
    def summarize(self, segment: str, items: list[NewsItem], part_index: int = 1, part_total: int = 1) -> str:
        lines = [f"[DRY RUN] {segment} part {part_index}/{part_total}"]
        for item in items:
            lines.append(f"- {item.title}: {item.url}")
        return "\n".join(lines)
