import argparse

from app.config import get_settings
from app.telegram import TelegramClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["set"])
    args = parser.parse_args()
    settings = get_settings()
    if args.action == "set":
        url = f"{settings.app_base_url.rstrip('/')}/telegram/webhook/{settings.telegram_webhook_secret}"
        result = TelegramClient(settings.telegram_bot_token).set_webhook(url)
        print(result)


if __name__ == "__main__":
    main()

