#!/usr/bin/env python3
"""
Index a single transcription markdown file into the project's FAISS vector store
using NVIDIA embeddings.

Usage:
    python scripts/index_single_file.py /path/to/transcription_transcription_made.md

Environment vars required:
  - NVIDIA_EMBEDDING_API_KEY
  - NVIDIA_BASE_URL (optional, defaults to https://integrate.api.nvidia.com/v1)

This script uses the project's `VectorStore` and `TranscriptionIndexer` classes.
"""
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.agent.vector_store import VectorStore
from src.agent.transcription_indexer import TranscriptionIndexer


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/index_single_file.py /path/to/file.md")
        return 1

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    # Ensure API key exists
    if not os.getenv("NVIDIA_EMBEDDING_API_KEY"):
        print("ERROR: NVIDIA_EMBEDDING_API_KEY not set. Export it before running.")
        return 1

    print(f"Indexing file: {file_path}")

    # Initialize vector store
    vs = VectorStore()  # uses env var NVIDIA_EMBEDDING_API_KEY

    # Use TranscriptionIndexer to process and index file
    indexer = TranscriptionIndexer(vector_store=vs, source_dir=str(file_path.parent))

    result = indexer.index_transcription(file_path)

    print("Indexed:", result)
    print("Total documents in vector store:", len(vs))

    return 0


if __name__ == '__main__':
    sys.exit(main())