# AI News Telegram Bot

FastAPI Telegram bot that monitors AI news sources, dedupes new items in MongoDB Atlas, summarizes them with Gemini 2.5 Flash through Lightning AI, and sends scheduled Telegram updates to users who send `/start`.

## What It Sends

All times are IST.

| Segment | Time |
| --- | --- |
| Daily Dose of DS newsletter | 9:00 AM daily |
| Big Tech AI News | 12:00 PM and 8:00 PM daily; noon sends the first half, evening sends the remaining half |
| AI Tool Drop | 12:00 PM, 6:00 PM, and 9:00 PM daily, only if new |
| AI GitHub Repo of the Day | 5:00 PM daily |
| Agent Harness Engineering | 7:00 PM daily |
| Model Releases | when a new release is detected |
| Prit Manvar Blog | when a new post is detected |
| Sebastian Raschka Blog | when a new post is detected |

## Setup

```powershell
uv sync --extra dev
Copy-Item .env.example .env
```

Fill `.env` with your Telegram bot token, Lightning AI key, MongoDB Atlas URI, Langfuse keys, and secrets.

Run locally:

```powershell
uv run uvicorn app.main:app --reload
```

Run a dry job:

```powershell
uv run python -m app.jobs tools --dry-run
uv run python -m app.jobs scheduled --dry-run
```

## Telegram Webhook

After deploying, set the webhook:

```powershell
uv run python -m app.telegram_webhook set
```

The webhook URL is:

```text
{APP_BASE_URL}/telegram/webhook/{TELEGRAM_WEBHOOK_SECRET}
```

## Source Configuration

Add or edit sources in `sources.yaml`. Supported source types:

- `rss` / `atom`
- `json`
- `html`
- `github_search`
- `github_trending_html`

DailyDoseofDS uses the public newsletter feed at `https://blog.dailydoseofds.com/feed`. This is the newsletter-style feed with issues like CopilotKit/Hermes, not the separate `www.dailydoseofds.com/rss/` course/article feed.

Every fetched item is normalized and assigned a stable `canonical_id`. MongoDB has a unique index on that ID, so already-seen links are skipped automatically.

## Prompts

Edit `prompts.yaml` to change the message style for each segment. To push local prompts to Langfuse:

```powershell
uv run python -m app.langfuse_prompts sync
```

At runtime the bot tries Langfuse prompts first, then falls back to `prompts.yaml` if Langfuse is unavailable.

## Free Scheduling

`.github/workflows/scheduled.yml` runs every 30 minutes. The router checks impromptu model/blog alerts and also runs the fixed IST schedule jobs when the current time matches.

## Dedupe Flow

Each fetched item gets a canonical ID from its normalized URL. MongoDB has a unique index on that ID. If the item was already sent, it is skipped before the LLM call. If it was inserted but not sent because a previous run failed, it is retried.
