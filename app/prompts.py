from pathlib import Path

import yaml

from app.config import Settings


PROMPT_PREFIX = "ai-news-bot"


class PromptBook:
    def __init__(self, path: Path, settings: Settings | None = None):
        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        self.system = raw.get("system", "")
        self.segments = raw.get("segments", {})
        self.settings = settings

    def prompt_for(self, segment: str) -> str:
        langfuse_prompt = self._prompt_from_langfuse(segment)
        if langfuse_prompt:
            return langfuse_prompt
        return self.segments.get(segment, self.segments.get("big_tech", "Summarize this item: {title}\n{url}"))

    def system_prompt(self) -> str:
        return self._prompt_from_langfuse("system") or self.system

    def _prompt_from_langfuse(self, name: str) -> str:
        if not self.settings or not self.settings.langfuse_enabled:
            return ""
        if not self.settings.langfuse_public_key or not self.settings.langfuse_secret_key:
            return ""
        try:
            from langfuse import Langfuse, get_client

            Langfuse(
                public_key=self.settings.langfuse_public_key,
                secret_key=self.settings.langfuse_secret_key,
                base_url=self.settings.langfuse_base_url,
            )
            client = get_client()
            prompt = client.get_prompt(
                f"{PROMPT_PREFIX}-{name}",
                type="text",
                label=self.settings.langfuse_prompt_label,
            )
            return str(prompt.prompt)
        except Exception as exc:
            print(f"langfuse_prompt_fallback name={name} error={exc}")
            return ""
