from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.models import NewsItem


class MongoStore:
    def __init__(self, uri: str, db_name: str):
        if not uri:
            raise ValueError("MONGODB_URI is required")
        self.client: MongoClient = MongoClient(uri)
        self.db: Database = self.client[db_name]

    @property
    def users(self) -> Collection:
        return self.db["users"]

    @property
    def items(self) -> Collection:
        return self.db["items"]

    @property
    def job_runs(self) -> Collection:
        return self.db["job_runs"]

    @property
    def source_states(self) -> Collection:
        return self.db["source_states"]

    def ensure_indexes(self) -> None:
        self.users.create_index([("chat_id", ASCENDING)], unique=True)
        self.users.create_index([("active", ASCENDING)])
        self.items.create_index([("canonical_id", ASCENDING)], unique=True)
        self.items.create_index([("segment", ASCENDING), ("sent_at", ASCENDING)])
        self.job_runs.create_index([("job_name", ASCENDING), ("started_at", ASCENDING)])
        self.source_states.create_index([("source_id", ASCENDING), ("segment", ASCENDING)], unique=True)

    def upsert_user(self, telegram_user: dict[str, Any], chat: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        self.users.update_one(
            {"chat_id": chat["id"]},
            {
                "$set": {
                    "chat_id": chat["id"],
                    "telegram_user_id": telegram_user.get("id"),
                    "username": telegram_user.get("username"),
                    "first_name": telegram_user.get("first_name"),
                    "last_name": telegram_user.get("last_name"),
                    "chat_type": chat.get("type"),
                    "active": True,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    def active_chat_ids(self) -> list[int]:
        return [doc["chat_id"] for doc in self.users.find({"active": True}, {"chat_id": 1})]

    def mark_user_inactive(self, chat_id: int, reason: str) -> None:
        self.users.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "active": False,
                    "inactive_reason": reason,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

    def insert_item_if_new(self, item: NewsItem) -> bool:
        document = item.model_dump()
        document["sent_at"] = None
        try:
            self.items.insert_one(document)
            return True
        except DuplicateKeyError:
            existing = self.items.find_one({"canonical_id": item.canonical_id}, {"sent_at": 1})
            return bool(existing and existing.get("sent_at") is None)

    def mark_item_seen_without_sending(self, item: NewsItem, reason: str) -> None:
        document = item.model_dump()
        now = datetime.now(timezone.utc)
        document["sent_at"] = now
        document["skipped_at"] = now
        document["skipped_reason"] = reason
        try:
            self.items.insert_one(document)
        except DuplicateKeyError:
            return

    def mark_item_sent(self, canonical_id: str) -> None:
        self.items.update_one(
            {"canonical_id": canonical_id},
            {"$set": {"sent_at": datetime.now(timezone.utc)}},
        )

    def has_successful_job_run_since(self, job_name: str, since: datetime) -> bool:
        return bool(
            self.job_runs.find_one(
                {
                    "job_name": job_name,
                    "status": "ok",
                    "started_at": {"$gte": since},
                },
                {"_id": 1},
            )
        )

    def is_source_initialized(self, source_id: str, segment: str) -> bool:
        return bool(self.source_states.find_one({"source_id": source_id, "segment": segment}, {"_id": 1}))

    def mark_source_initialized(self, source_id: str, segment: str) -> None:
        now = datetime.now(timezone.utc)
        self.source_states.update_one(
            {"source_id": source_id, "segment": segment},
            {
                "$set": {"updated_at": now},
                "$setOnInsert": {"initialized_at": now},
            },
            upsert=True,
        )

    def log_job_run(
        self,
        job_name: str,
        status: str,
        counts: dict[str, int] | None = None,
        error: str = "",
    ) -> None:
        self.job_runs.insert_one(
            {
                "job_name": job_name,
                "status": status,
                "counts": counts or {},
                "error": error,
                "started_at": datetime.now(timezone.utc),
            }
        )
