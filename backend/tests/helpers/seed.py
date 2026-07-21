"""
seed.py - Helpers to seed and clean SQLite test data.

Used by fixture-based tests to insert sample transcriptions and clean them
up automatically after the test finishes. The SpeechNotes backend uses
SQLite (via SQLiteManager) as its primary store, so tests must seed the
same SQLite database the backend is reading from.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_test_id(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def default_db_path() -> str:
    """Resolve the path to the SQLite database the backend is using.

    Mirrors src/database/sqlite_manager.py:97-100:
        db_dir = os.getenv("SQLITE_DB_DIR", "data")
        self._db_path = os.path.join(db_dir, "speechnotes.db")
    """
    db_dir = os.environ.get("SQLITE_DB_DIR", "data")
    return os.path.join(db_dir, "speechnotes.db")


def connect_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open a connection to the test SQLite database.

    Use check_same_thread=False so the connection can be used from
    multiple threads (matches SQLiteManager default).
    """
    path = db_path or default_db_path()
    # Make sure the directory exists
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Apply the same schema as the backend (idempotent CREATE IF NOT EXISTS)
    _apply_schema(conn)
    return conn


def _apply_schema(conn: sqlite3.Connection) -> None:
    """Create the transcriptions + segments tables if they don't exist.

    Mirrors src/database/sqlite_manager.py:36-71.
    """
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS transcriptions (
            id               TEXT PRIMARY KEY,
            filename         TEXT UNIQUE NOT NULL,
            raw_content      TEXT NOT NULL DEFAULT '',
            date             TEXT,
            time             TEXT,
            word_count       INTEGER DEFAULT 0,
            source_type      TEXT DEFAULT 'live_recording',
            source_filename  TEXT,
            processed        INTEGER DEFAULT 0,
            ingested_at      TEXT,
            is_deleted       INTEGER DEFAULT 0,
            edited_content   TEXT,
            formatted_content TEXT
        );
        CREATE TABLE IF NOT EXISTS segments (
            id                TEXT PRIMARY KEY,
            transcription_id  TEXT NOT NULL,
            timestamp         TEXT DEFAULT '00:00:00',
            content           TEXT NOT NULL DEFAULT '',
            sequence          INTEGER DEFAULT 0,
            topic_title       TEXT,
            topic_summary     TEXT,
            embedded          INTEGER DEFAULT 0,
            FOREIGN KEY (transcription_id) REFERENCES transcriptions(id)
        );
        """
    )
    conn.commit()


def insert_transcription(
    conn: sqlite3.Connection,
    *,
    doc_id: Optional[str] = None,
    filename: Optional[str] = None,
    raw_content: str = "",
    formatted_content: str = "",
    edited_content: str = "",
    processed: bool = True,
) -> str:
    """Insert a test transcription and return its id."""
    final_id = doc_id or make_test_id("trans")
    final_filename = filename or f"{final_id}.md"
    # Note: we don't use is_test column (SQLiteManager doesn't define it),
    # so we rely on filename prefix 'test-' or 'trans-' to identify test rows.
    # Cleanup uses the same prefix logic.
    conn.execute(
        """
        INSERT OR REPLACE INTO transcriptions
            (id, filename, raw_content, formatted_content, edited_content,
             date, ingested_at, is_deleted, processed)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (
            final_id,
            final_filename,
            raw_content,
            formatted_content,
            edited_content,
            now_iso(),
            now_iso(),
            1 if processed else 0,
        ),
    )
    conn.commit()
    return final_id


def delete_transcription(conn: sqlite3.Connection, doc_id: str) -> int:
    cur = conn.execute("DELETE FROM transcriptions WHERE id = ?", (doc_id,))
    conn.commit()
    return cur.rowcount


def count_test_transcriptions(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM transcriptions WHERE id LIKE 'test-%' OR id LIKE 'trans-test-%'"
    ).fetchone()
    return row["c"] if row else 0


def cleanup_test_transcriptions(conn: sqlite3.Connection) -> int:
    """Remove every transcription inserted by tests (id starts with 'test-' or 'trans-')."""
    cur = conn.execute(
        "DELETE FROM transcriptions WHERE id LIKE 'test-%' OR id LIKE 'trans-test-%'"
    )
    conn.commit()
    return cur.rowcount


def db_available(db_path: Optional[str] = None) -> bool:
    """Return True if the SQLite file is accessible (always True unless FS error)."""
    try:
        path = db_path or default_db_path()
        # Make sure the directory exists
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        conn = sqlite3.connect(path, timeout=2.0)
        conn.execute("SELECT 1").fetchone()
        conn.close()
        return True
    except Exception:
        return False
