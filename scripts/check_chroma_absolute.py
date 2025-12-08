#!/usr/bin/env python3
"""
Check Chroma DB via chromadb.Client using an absolute persist directory.

Usage:
  python scripts/check_chroma_absolute.py
"""
import os
import sys
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:
    print("chromadb not installed or import failed:", e, file=sys.stderr)
    sys.exit(2)

# Absolute path to the chroma DB (adjusted for this workspace)
ABS_DB = Path(r"c:\Users\gamur\OneDrive - UNIVERSIDAD DE LAS FUERZAS ARMADAS ESPE\ESPE VI NIVEL SII2025\Analisis y Diseño\p\knowledge_base\chroma_db")

def main():
    if not ABS_DB.exists():
        print(f"Absolute Chroma DB path not found: {ABS_DB}")
        sys.exit(1)

    print(f"Opening Chroma DB at absolute path: {ABS_DB}")
    try:
        client = chromadb.Client(Settings(persist_directory=str(ABS_DB)))
    except Exception as e:
        print("Failed to open Chroma client:", e)
        sys.exit(3)

    try:
        cols = client.list_collections()
    except Exception as e:
        print("Failed to list collections via client:", e)
        sys.exit(4)

    if not cols:
        print("Chroma client reports: No collections found.")
        return

    print("Collections returned by client:")
    for c in cols:
        # c may be dict or object
        name = c.get('name') if isinstance(c, dict) else getattr(c, 'name', str(c))
        print(f" - {name}")
        try:
            collection = client.get_collection(name=name)
            res = collection.get(limit=1, include=['embeddings','ids'])
            ids = res.get('ids') or []
            emb = res.get('embeddings') or []
            count = len(ids)
            if emb and len(emb) > 0:
                dim = len(emb[0])
                print(f"    Items (sampled): {count} | Embedding dim: {dim}")
            else:
                print(f"    Items (sampled): {count} | No embeddings in sample")
        except Exception as e:
            print(f"    Failed to inspect collection {name}: {e}")

if __name__ == '__main__':
    main()
