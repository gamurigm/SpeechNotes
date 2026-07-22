import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure optional dependencies are mocked if missing
for mod in ["dotenv", "numpy", "openai", "faiss"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from src.agent.transcription_indexer import TranscriptionIndexer


def test_load_metadata_default_if_not_exists(tmp_path):
    mock_vs = MagicMock()
    indexer = TranscriptionIndexer(vector_store=mock_vs, source_dir=str(tmp_path), processed_dir=str(tmp_path / "proc"))
    
    metadata = indexer._load_metadata()
    assert metadata == {"indexed_files": {}, "last_update": None}


def test_save_and_load_metadata(tmp_path):
    mock_vs = MagicMock()
    proc_dir = tmp_path / "proc"
    indexer = TranscriptionIndexer(vector_store=mock_vs, source_dir=str(tmp_path), processed_dir=str(proc_dir))
    
    indexer.index_metadata["indexed_files"]["test.md"] = {"mtime": 100}
    indexer._save_metadata()
    
    assert (proc_dir / "index_metadata.json").exists()
    loaded = indexer._load_metadata()
    assert "test.md" in loaded["indexed_files"]


def test_create_chunks_splits_sections():
    mock_vs = MagicMock()
    indexer = TranscriptionIndexer.__new__(TranscriptionIndexer)
    
    content = """## Tema 1: Introducción
**⏱️ Timestamp**: 00:00:00
Esta es la primera parte de la lección sobre inteligencia artificial.

## Tema 2: Redes Neuronales
**⏱️ Timestamp**: 00:10:00
Esta es la segunda parte de la lección sobre aprendizaje profundo."""

    metadata = {"filename": "clase.md", "date": "2026-07-22"}
    chunks = indexer._create_chunks(content, metadata, chunk_size=50)
    
    assert len(chunks) == 2
    assert chunks[0]["metadata"]["topic"] == "Introducción"
    assert chunks[1]["metadata"]["topic"] == "Redes Neuronales"
