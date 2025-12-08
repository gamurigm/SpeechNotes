#!/usr/bin/env python3
"""
Inspect the Chroma sqlite database to list tables and sample content.

Usage:
  python scripts/inspect_chroma_sqlite.py
"""
import os
import sqlite3
from pathlib import Path

DB_PATH = Path("knowledge_base") / "chroma_db" / "chroma.sqlite3"

def main():
    if not DB_PATH.exists():
        print(f"SQLite DB not found at {DB_PATH}")
        return

    print(f"Opening SQLite DB: {DB_PATH}\n")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables:")
    for t in tables:
        print(f" - {t}")

    # Print counts for known tables
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
            print(f"Table {t}: {count} rows")
        except Exception as e:
            print(f"  Could not count rows for {t}: {e}")

    # Show sample from 'collections' or similar
    sample_tables = [t for t in tables if 'collection' in t or 'collections' in t or 'metadata' in t]
    if sample_tables:
        for t in sample_tables:
            print(f"\nSample rows from {t}:")
            try:
                cur.execute(f"SELECT * FROM {t} LIMIT 5")
                rows = cur.fetchall()
                for r in rows:
                    print(r)
            except Exception as e:
                print(f"  Failed to fetch sample: {e}")

    conn.close()

if __name__ == '__main__':
    main()
