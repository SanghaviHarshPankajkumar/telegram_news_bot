import httpx
import re
from html import escape


WELCOME_MESSAGE = """Welcome to AI News Bot.

You are subscribed to:
- Daily Dose of DS: 9:00 AM IST
- Big Tech AI News: 12:00 PM and 8:00 PM IST
- AI Tool Drops: 12:00 PM, 6:00 PM, 9:00 PM IST when new
- AI Repo of the Day: 5:00 PM IST
- Agent Harness Engineering: 7:00 PM IST
- New model releases: summary when detected
- Prit Manvar and Sebastian Raschka blogs: summary when detected
"""

SECTION_HEADERS = {
    "today's lineup",
    "lineup",
    "section summaries",
    "main takeaways",
    "builder note",
    "links",
    "what changed",
    "nvidia",
    "openai",
    "anthropic",
    "xai",
    "microsoft",
    "policy and markets",
    "infrastructure and hardware",
    "models and products",
    "robotics and physical ai",
    "other important ai updates",
    "why it matters",
    "watch next",
    "what it does",
    "best fit",
    "access/pricing",
    "why it is useful",
    "try this",
    "signal",
    "release notes",
    "builder impact",
    "core idea",
    "builder takeaway",
    "today's concept",
    "how to use it",
    "failure mode to watch",
}


def markdown_to_telegram_html(text: str) -> str:
    escaped_lines = []
    for index, line in enumerate(text.splitlines()):
        line = re.sub(r"^(\s*)-\s+", r"\1• ", line)
        line = re.sub(r"^(\s*)\*\s+", r"\1• ", line)
        escaped = escape(line)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", escaped)
        normalized = line.strip().rstrip(":").lower()
        if escaped.strip() and (index == 0 or normalized in SECTION_HEADERS):
            escaped = f"<b>{escaped}</b>"
        escaped_lines.append(escaped)
    return "\n".join(escaped_lines)


class TelegramClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, chat_id: int, text: str) -> None:
        html_text = markdown_to_telegram_html(text)[:3900]
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": html_text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
            )
            if response.status_code == 400:
                response = client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text[:3900],
                        "disable_web_page_preview": False,
                    },
                )
        response.raise_for_status()

    def set_webhook(self, webhook_url: str) -> dict:
        with httpx.Client(timeout=30) as client:
            response = client.post(f"{self.base_url}/setWebhook", json={"url": webhook_url})
        response.raise_for_status()
        return response.json()
