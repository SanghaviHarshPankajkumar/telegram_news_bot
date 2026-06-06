from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    app_base_url: str = ""
    lightning_api_key: str = ""
    lightning_base_url: str = "https://lightning.ai/api/v1/"
    lightning_model: str = "google/gemini-2.5-flash"
    mongodb_uri: str = ""
    mongodb_db: str = "ai_news_bot"
    job_secret: str = ""
    timezone: str = "Asia/Kolkata"
    github_token: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_prompt_label: str = "production"
    langfuse_enabled: bool = True
    sources_path: Path = Field(default=Path("sources.yaml"))
    prompts_path: Path = Field(default=Path("prompts.yaml"))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
