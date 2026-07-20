"""
seed.py - Helpers to seed and clean MongoDB test data.

Used by fixture-based tests to insert sample transcriptions / documents
and clean them up automatically after the test finishes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_test_id(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def connect_mongo(uri: str, db_name: str) -> MongoClient:
    return MongoClient(uri, serverSelectionTimeoutMS=3000)


def insert_transcription(
    mongo: MongoClient,
    db_name: str,
    *,
    doc_id: Optional[str] = None,
    filename: Optional[str] = None,
    raw_content: str = "",
    formatted_content: str = "",
    edited_content: str = "",
    processed: bool = True,
) -> str:
    """Insert a test transcription and return its _id."""
    db = mongo[db_name]
    final_id = doc_id or make_test_id("trans")
    final_filename = filename or f"{final_id}.md"
    doc = {
        "_id": final_id,
        "filename": final_filename,
        "date": now_iso(),
        "ingested_at": now_iso(),
        "is_deleted": False,
        "is_test": True,
        "processed": processed,
        "raw_content": raw_content,
        "formatted_content": formatted_content,
        "edited_content": edited_content,
    }
    db["transcriptions"].insert_one(doc)
    return final_id


def delete_transcription(mongo: MongoClient, db_name: str, doc_id: str) -> int:
    db = mongo[db_name]
    result = db["transcriptions"].delete_one({"_id": doc_id})
    return result.deleted_count


def count_test_transcriptions(mongo: MongoClient, db_name: str) -> int:
    db = mongo[db_name]
    return db["transcriptions"].count_documents({"is_test": True})


def cleanup_test_transcriptions(mongo: MongoClient, db_name: str) -> int:
    """Remove every transcription inserted by tests (is_test=True)."""
    db = mongo[db_name]
    result = db["transcriptions"].delete_many({"is_test": True})
    return result.deleted_count


def mongo_available(uri: str) -> bool:
    """Return True if Mongo is reachable, False otherwise (never raises)."""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False
    except Exception:
        return False
