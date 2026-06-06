from fastapi import FastAPI, HTTPException, Request

from app.config import get_settings
from app.langfuse_prompts import configure_langfuse
from app.repository import MongoStore
from app.telegram import TelegramClient, WELCOME_MESSAGE

app = FastAPI(title="AI News Telegram Bot")


@app.on_event("startup")
def startup() -> None:
    settings = get_settings()
    configure_langfuse(settings)
    if settings.mongodb_uri:
        store = MongoStore(settings.mongodb_uri, settings.mongodb_db)
        store.ensure_indexes()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> dict[str, bool]:
    settings = get_settings()
    if secret != settings.telegram_webhook_secret:
        raise HTTPException(status_code=404, detail="Not found")

    update = await request.json()
    message = update.get("message") or update.get("edited_message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    user = message.get("from") or {}
    if not chat:
        return {"ok": True}

    if text.startswith("/start"):
        store = MongoStore(settings.mongodb_uri, settings.mongodb_db)
        store.ensure_indexes()
        store.upsert_user(user, chat)
        TelegramClient(settings.telegram_bot_token).send_message(chat["id"], WELCOME_MESSAGE)
    return {"ok": True}
