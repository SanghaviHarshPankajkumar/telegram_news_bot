from __future__ import annotations

import argparse
import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.ai import DryRunSummarizer, Summarizer
from app.config import get_settings
from app.filters import matches_filters, matches_segment_defaults, segment_score
from app.langfuse_prompts import configure_langfuse
from app.models import NewsItem
from app.prompts import PromptBook
from app.repository import MongoStore
from app.source_loader import load_sources, sources_for_segment
from app.sources import fetch_source
from app.telegram import TelegramClient

JOB_LIMITS = {
    "daily_dose_ds": 1,
    "big_tech": 200,
    "big_tech_noon": 200,
    "big_tech_evening": 200,
    "tools": 1,
    "github_repo": 1,
    "model_releases": 3,
    "prit_blog": 1,
    "sebastian_blog": 1,
    "agent_harness_engineering": 1,
    "agent_learning": 1,
}

SCHEDULED_JOBS = {
    "09:00": ["daily_dose_ds"],
    "12:00": ["big_tech_noon", "tools"],
    "17:00": ["github_repo"],
    "18:00": ["tools"],
    "19:00": ["agent_harness_engineering"],
    "20:00": ["big_tech_evening"],
    "21:00": ["tools"],
}

EVERY_POLL_JOBS = ["model_releases", "prit_blog", "sebastian_blog"]
FRESH_ONLY_JOBS = set(JOB_LIMITS)
BIG_TECH_ITEMS_PER_MESSAGE = 10
SCHEDULE_CATCHUP_MINUTES = 20

JOB_SOURCE_SEGMENTS = {
    "big_tech_noon": "big_tech",
    "big_tech_evening": "big_tech",
}

JOB_PROMPT_SEGMENTS = {
    "big_tech_noon": "big_tech",
    "big_tech_evening": "big_tech",
}


def select_big_tech_items(job_name: str, items: list[NewsItem]) -> list[NewsItem]:
    sorted_items = sorted(items, key=lambda item: item.published_at or item.first_seen_at, reverse=True)
    if job_name == "big_tech_noon":
        return sorted_items[: math.ceil(len(sorted_items) / 2)]
    if job_name == "big_tech_evening":
        return sorted_items
    return sorted_items


def chunk_items(items: list[NewsItem], chunk_size: int) -> list[list[NewsItem]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def fresh_cutoff_for_today(timezone_name: str, now: datetime | None = None) -> datetime:
    local_now = (now or datetime.now(tz=ZoneInfo("UTC"))).astimezone(ZoneInfo(timezone_name))
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight.astimezone(ZoneInfo("UTC"))


def is_fresh_for_impromptu(segment: str, item: NewsItem, settings_timezone: str, now: datetime | None = None) -> bool:
    if segment not in FRESH_ONLY_JOBS:
        return True
    if not item.published_at:
        return False
    return item.published_at >= fresh_cutoff_for_today(settings_timezone, now)


def collect_new_items(
    segment: str,
    store: MongoStore | None,
    dry_run: bool,
    limit: int | None = None,
) -> list[NewsItem]:
    settings = get_settings()
    sources = sources_for_segment(load_sources(settings.sources_path), segment)
    collected: list[NewsItem] = []
    max_items = limit or JOB_LIMITS.get(segment, 1)
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "ai-news-bot/0.1"}) as client:
        for source in sources:
            try:
                items = list(fetch_source(client, source, segment, settings.github_token))
            except Exception as exc:
                print(f"source_failed source={source.id} error={exc}")
                continue
            items = sorted(items, key=lambda item: segment_score(item, segment), reverse=True)
            for item in items:
                if not matches_filters(item, source):
                    continue
                if not matches_segment_defaults(item, segment):
                    continue
                if not is_fresh_for_impromptu(segment, item, settings.timezone):
                    continue
                if dry_run:
                    collected.append(item)
                elif store and store.insert_item_if_new(item):
                    collected.append(item)
                if len(collected) >= max_items:
                    return collected
    return collected


def broadcast(text: str, items: list[NewsItem], store: MongoStore, dry_run: bool) -> None:
    if dry_run:
        print(text)
        return

    telegram = TelegramClient(get_settings().telegram_bot_token)
    for chat_id in store.active_chat_ids():
        try:
            telegram.send_message(chat_id, text)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {400, 403}:
                store.mark_user_inactive(chat_id, f"telegram_{exc.response.status_code}")
            else:
                raise
    for item in items:
        store.mark_item_sent(item.canonical_id)


def run_job(job_name: str, dry_run: bool = False, limit: int | None = None) -> int:
    settings = get_settings()
    configure_langfuse(settings)
    store = None if dry_run else MongoStore(settings.mongodb_uri, settings.mongodb_db)
    if store:
        store.ensure_indexes()

    try:
        source_segment = JOB_SOURCE_SEGMENTS.get(job_name, job_name)
        summary_segment = JOB_PROMPT_SEGMENTS.get(job_name, job_name)
        items = collect_new_items(source_segment, store, dry_run, limit)
        if job_name in {"big_tech_noon", "big_tech_evening"} and items:
            items = select_big_tech_items(job_name, items)
        if job_name == "agent_harness_engineering" and not items:
            print("agent_harness_engineering: no fresh agent news, using learning fallback")
            items = collect_new_items("agent_learning", store, dry_run, limit or 1)
            summary_segment = "agent_harness_engineering"
        if not items:
            print(f"{job_name}: no new items")
            if store:
                store.log_job_run(job_name, "ok", {"new_items": 0, "sent": 0})
            return 0

        summarizer = DryRunSummarizer() if dry_run else Summarizer(
            settings.lightning_api_key,
            settings.lightning_base_url,
            settings.lightning_model,
            PromptBook(settings.prompts_path, settings),
            settings,
        )
        item_chunks = [items]
        if summary_segment == "big_tech":
            item_chunks = chunk_items(items, BIG_TECH_ITEMS_PER_MESSAGE)

        for index, chunk in enumerate(item_chunks, start=1):
            text = summarizer.summarize(
                summary_segment,
                chunk,
                part_index=index,
                part_total=len(item_chunks),
            )
            if store:
                broadcast(text, chunk, store, dry_run)
            else:
                broadcast(text, chunk, store, dry_run)  # type: ignore[arg-type]
        if store:
            store.log_job_run(
                job_name,
                "ok",
                {
                    "new_items": len(items),
                    "sent": len(items),
                    "messages": len(item_chunks),
                },
            )
        return 0
    except Exception as exc:
        if store:
            store.log_job_run(job_name, "error", error=str(exc))
        raise


def due_jobs(now: datetime, store: MongoStore | None = None) -> list[str]:
    timezone = ZoneInfo(get_settings().timezone)
    local = now.astimezone(timezone)
    key = local.strftime("%H:%M")
    jobs = list(EVERY_POLL_JOBS)

    if store is None:
        jobs.extend(SCHEDULED_JOBS.get(key, []))
        return jobs

    for scheduled_time, scheduled_jobs in SCHEDULED_JOBS.items():
        scheduled_clock = time.fromisoformat(scheduled_time)
        scheduled_local = datetime.combine(local.date(), scheduled_clock, tzinfo=timezone)
        if local < scheduled_local:
            continue
        if local - scheduled_local > timedelta(minutes=SCHEDULE_CATCHUP_MINUTES):
            continue
        scheduled_utc = scheduled_local.astimezone(ZoneInfo("UTC"))
        for job in scheduled_jobs:
            if not store.has_successful_job_run_since(job, scheduled_utc):
                jobs.append(job)
    return jobs


def run_scheduled(dry_run: bool = False) -> int:
    settings = get_settings()
    store = None if dry_run else MongoStore(settings.mongodb_uri, settings.mongodb_db)
    if store:
        store.ensure_indexes()
    jobs = due_jobs(datetime.now(tz=ZoneInfo("UTC")), store)
    print(f"scheduled jobs: {', '.join(jobs)}")
    exit_code = 0
    for job in jobs:
        exit_code = max(exit_code, run_job(job, dry_run=dry_run))
    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "job_name",
        choices=[*JOB_LIMITS.keys(), "scheduled"],
        help="Job to run.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print selected items without sending Telegram messages.")
    parser.add_argument("--limit", type=int, default=None, help="Override item limit for this run.")
    args = parser.parse_args()

    if args.job_name == "scheduled":
        raise SystemExit(run_scheduled(dry_run=args.dry_run))
    raise SystemExit(run_job(args.job_name, dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()
