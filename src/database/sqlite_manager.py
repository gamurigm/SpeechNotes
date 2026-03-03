"""
SQLite Manager Module
Replaces MongoManager for the desktop app.
Handles connection and operations with SQLite.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_id() -> str:
    """Generate a unique string ID (replaces MongoDB ObjectId)."""
    return uuid.uuid4().hex


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a sqlite3.Row to a plain dict."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
-- Transcriptions table (mirrors former MongoDB 'transcriptions' collection)
CREATE TABLE IF NOT EXISTS transcriptions (
    id               TEXT PRIMARY KEY,
    filename         TEXT UNIQUE NOT NULL,
    raw_content      TEXT NOT NULL DEFAULT '',
    date             TEXT,
    time             TEXT,
    word_count       INTEGER DEFAULT 0,
    source_type      TEXT DEFAULT 'live_recording',
    source_filename  TEXT,
    processed        INTEGER DEFAULT 0,       -- boolean 0/1
    ingested_at      TEXT,
    is_deleted       INTEGER DEFAULT 0,       -- boolean 0/1
    edited_content   TEXT,
    formatted_content TEXT
);

-- Segments table (mirrors former MongoDB 'segments' collection)
CREATE TABLE IF NOT EXISTS segments (
    id                TEXT PRIMARY KEY,
    transcription_id  TEXT NOT NULL,
    timestamp         TEXT DEFAULT '00:00:00',
    content           TEXT NOT NULL DEFAULT '',
    sequence          INTEGER DEFAULT 0,
    topic_title       TEXT,
    topic_summary     TEXT,
    embedded          INTEGER DEFAULT 0,       -- boolean 0/1
    FOREIGN KEY (transcription_id) REFERENCES transcriptions(id)
);

CREATE INDEX IF NOT EXISTS idx_segments_txn ON segments(transcription_id);
CREATE INDEX IF NOT EXISTS idx_segments_embedded ON segments(embedded);
CREATE INDEX IF NOT EXISTS idx_transcriptions_processed ON transcriptions(processed);
CREATE INDEX IF NOT EXISTS idx_transcriptions_deleted ON transcriptions(is_deleted);
"""


# ---------------------------------------------------------------------------
# SQLiteManager (Singleton, drop-in replacement for MongoManager)
# ---------------------------------------------------------------------------

class SQLiteManager:
    """
    Singleton class to manage the local SQLite database.

    Public API intentionally mirrors MongoManager so that consumers
    (TranscriptionRepository, Ingestor, Analyzer, Embedder, etc.)
    need minimal changes.
    """

    _instance: Optional["SQLiteManager"] = None

    def __new__(cls) -> "SQLiteManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    # ---- lifecycle --------------------------------------------------------

    def _initialize(self) -> None:
        db_dir = os.getenv("SQLITE_DB_DIR", "data")
        Path(db_dir).mkdir(parents=True, exist_ok=True)
        self._db_path = os.path.join(db_dir, "speechnotes.db")

        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        # Create tables if first run
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()
        print(f"[INFO] SQLite connected at {self._db_path}")

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            print("[INFO] SQLite connection closed")

    # ---- collection-like accessors (compatibility layer) ------------------

    @property
    def transcriptions(self) -> "TranscriptionsTable":
        return TranscriptionsTable(self._conn)

    @property
    def segments(self) -> "SegmentsTable":
        return SegmentsTable(self._conn)


# ---------------------------------------------------------------------------
# Thin wrappers that emulate pymongo Collection CRUD (find, find_one, etc.)
# ---------------------------------------------------------------------------

class _BaseTable:
    """Shared helpers for both transcriptions and segments tables."""

    TABLE: str = ""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _id_field() -> str:
        return "id"

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur

    def _row_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        # Alias 'id' → '_id' so consumers written for Mongo keep working
        if "id" in d:
            d["_id"] = d["id"]
        return d

    # -- public pymongo-style API ------------------------------------------

    def find_one(self, filter_dict: Optional[Dict] = None, **kwargs) -> Optional[Dict]:
        where, params = self._build_where(filter_dict or {})
        sort_clause = self._build_sort(kwargs.get("sort"))
        sql = f"SELECT * FROM {self.TABLE} {where} {sort_clause} LIMIT 1"
        row = self._conn.execute(sql, params).fetchone()
        return self._row_dict(row) if row else None

    def find(self, filter_dict: Optional[Dict] = None, **kwargs) -> "_Cursor":
        where, params = self._build_where(filter_dict or {})
        sql = f"SELECT * FROM {self.TABLE} {where}"
        return _Cursor(self._conn, sql, params, self._row_dict)

    def insert_one(self, doc: Dict) -> "_InsertResult":
        doc = dict(doc)  # copy
        doc_id = doc.pop("_id", None) or doc.pop("id", None) or _generate_id()
        doc["id"] = doc_id
        cols = ", ".join(doc.keys())
        placeholders = ", ".join(["?"] * len(doc))
        self._execute(
            f"INSERT OR IGNORE INTO {self.TABLE} ({cols}) VALUES ({placeholders})",
            tuple(doc.values()),
        )
        return _InsertResult(doc_id)

    def insert_many(self, docs: List[Dict]) -> int:
        count = 0
        for doc in docs:
            self.insert_one(doc)
            count += 1
        return count

    def update_one(self, filter_dict: Dict, update: Dict) -> "_UpdateResult":
        set_fields = update.get("$set", update)
        set_clause = ", ".join(f"{k}=?" for k in set_fields)
        set_values = list(set_fields.values())
        where, where_params = self._build_where(filter_dict)
        sql = f"UPDATE {self.TABLE} SET {set_clause} {where}"
        cur = self._execute(sql, tuple(set_values) + where_params)
        return _UpdateResult(cur.rowcount, cur.rowcount)

    def update_many(self, filter_dict: Dict, update: Dict) -> "_UpdateResult":
        return self.update_one(filter_dict, update)  # same logic, no LIMIT 1

    def count_documents(self, filter_dict: Optional[Dict] = None) -> int:
        where, params = self._build_where(filter_dict or {})
        row = self._conn.execute(
            f"SELECT COUNT(*) as c FROM {self.TABLE} {where}", params
        ).fetchone()
        return row["c"] if row else 0

    # -- filter builder ----------------------------------------------------

    def _build_where(self, f: Dict) -> tuple:
        """Translate a Mongo-style filter dict into SQL WHERE + params."""
        clauses: List[str] = []
        params: List[Any] = []

        for key, value in f.items():
            if key == "$or":
                or_parts = []
                for sub in value:
                    sub_clause, sub_params = self._build_where(sub)
                    or_parts.append(sub_clause.replace("WHERE ", ""))
                    params.extend(sub_params)
                if or_parts:
                    clauses.append(f"({' OR '.join(or_parts)})")
                continue

            # Normalise _id → id
            col = "id" if key == "_id" else key

            if isinstance(value, dict):
                for op, operand in value.items():
                    if op == "$ne":
                        if operand is True:
                            clauses.append(f"({col} IS NULL OR {col} != 1)")
                        else:
                            clauses.append(f"{col} != ?")
                            params.append(operand)
                    elif op == "$regex":
                        clauses.append(f"{col} LIKE ?")
                        # Convert basic regex to LIKE (good enough for simple patterns)
                        params.append(f"%{operand}%")
                    elif op == "$in":
                        placeholders = ",".join(["?"] * len(operand))
                        clauses.append(f"{col} IN ({placeholders})")
                        params.extend(operand)
                    elif op == "$options":
                        pass  # LIKE is case-insensitive by default in SQLite
            else:
                # Handle boolean → int
                if isinstance(value, bool):
                    value = int(value)
                clauses.append(f"{col} = ?")
                params.append(value)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return where, tuple(params)

    @staticmethod
    def _build_sort(sort_spec) -> str:
        if not sort_spec:
            return ""
        if isinstance(sort_spec, list):
            parts = []
            for col, direction in sort_spec:
                col = "id" if col == "_id" else col
                parts.append(f"{col} {'ASC' if direction == 1 else 'DESC'}")
            return "ORDER BY " + ", ".join(parts)
        return ""


class TranscriptionsTable(_BaseTable):
    TABLE = "transcriptions"


class SegmentsTable(_BaseTable):
    TABLE = "segments"


# ---------------------------------------------------------------------------
# Tiny result wrappers
# ---------------------------------------------------------------------------

class _InsertResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class _UpdateResult:
    def __init__(self, matched: int, modified: int):
        self.matched_count = matched
        self.modified_count = modified


class _Cursor:
    """Lazy cursor that mimics pymongo Cursor (sort / limit / iteration)."""

    def __init__(self, conn, sql, params, row_mapper):
        self._conn = conn
        self._sql = sql
        self._params = params
        self._row_mapper = row_mapper
        self._sort_clause = ""
        self._limit_clause = ""

    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, str):
            col = "id" if key_or_list == "_id" else key_or_list
            d = "ASC" if direction == 1 else "DESC"
            self._sort_clause = f"ORDER BY {col} {d}"
        elif isinstance(key_or_list, list):
            parts = []
            for col, d in key_or_list:
                col = "id" if col == "_id" else col
                parts.append(f"{col} {'ASC' if d == 1 else 'DESC'}")
            self._sort_clause = "ORDER BY " + ", ".join(parts)
        return self

    def limit(self, n: int):
        self._limit_clause = f"LIMIT {n}"
        return self

    def _full_sql(self) -> str:
        return f"{self._sql} {self._sort_clause} {self._limit_clause}".strip()

    def __iter__(self):
        rows = self._conn.execute(self._full_sql(), self._params).fetchall()
        for row in rows:
            yield self._row_mapper(row)

    def __list__(self):
        return list(self.__iter__())
