#!/usr/bin/env python3
"""
Simple diagnostic for Chroma persistent DB.

Run from repository root to print collection names, stored embeddings dimension
and a sample item count. Useful to detect embedding-dimension mismatches.

Usage:
  python scripts/check_chroma_dim.py

"""
import os
import sys

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:
    print("Error: chromadb not available. Install with: pip install chromadb")
    raise

DB_DIR = os.path.join("knowledge_base", "chroma_db")

def main():
    if not os.path.exists(DB_DIR):
        print(f"Chroma DB path not found: {DB_DIR}")
        sys.exit(1)

    print(f"Opening Chroma DB at: {DB_DIR}")
    try:
        client = chromadb.Client(Settings(persist_directory=DB_DIR))
    except Exception as e:
        print("Failed to open Chroma client:", e)
        sys.exit(2)

    try:
        cols = client.list_collections()
    except Exception as e:
        print("Failed to list collections:", e)
        sys.exit(3)

    if not cols:
        print("No collections found in Chroma DB.")
        return

    for c in cols:
        # `list_collections` returns a list of dicts with 'name'
        name = c.get('name') if isinstance(c, dict) else str(c)
        print(f"\nCollection: {name}")
        try:
            collection = client.get_collection(name=name)
        except Exception as e:
            print("  Failed to open collection:", e)
            continue

        try:
            # Try to fetch one item including embeddings
            result = collection.get(limit=1, include=['embeddings','ids'])
        except Exception as e:
            print("  Failed to read collection contents:", e)
            continue

        ids = result.get('ids') or []
        emb = result.get('embeddings') or []
        count = len(ids)
        if emb and len(emb) > 0:
            dim = len(emb[0])
            print(f"  Items (sampled): {count} | Embedding dimension: {dim}")
        else:
            print(f"  Items (sampled): {count} | No embeddings found in sample")

if __name__ == '__main__':
    main()
