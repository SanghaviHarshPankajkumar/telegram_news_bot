from __future__ import annotations

import argparse

import yaml

from app.config import Settings, get_settings
from app.prompts import PROMPT_PREFIX


def configure_langfuse(settings: Settings) -> None:
    if not settings.langfuse_enabled:
        return
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return
    try:
        from langfuse import Langfuse

        Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_base_url,
        )
    except Exception as exc:
        print(f"langfuse_config_failed error={exc}")


def sync_prompts(settings: Settings) -> None:
    configure_langfuse(settings)
    from langfuse import get_client

    with settings.prompts_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    client = get_client()
    prompts = {"system": raw.get("system", "")}
    prompts.update(raw.get("segments", {}))

    for name, prompt in prompts.items():
        if not prompt:
            continue
        client.create_prompt(
            name=f"{PROMPT_PREFIX}-{name}",
            type="text",
            prompt=prompt,
            labels=[settings.langfuse_prompt_label],
        )
        print(f"synced {PROMPT_PREFIX}-{name}")
    client.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["sync"])
    args = parser.parse_args()
    if args.action == "sync":
        sync_prompts(get_settings())


if __name__ == "__main__":
    main()
