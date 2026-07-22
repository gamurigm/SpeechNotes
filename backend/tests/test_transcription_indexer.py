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


def test_load_metadata_returns_defaults_for_corrupt_file(tmp_path):
    proc = tmp_path / "proc"
    proc.mkdir()
    (proc / "index_metadata.json").write_text("{bad", encoding="utf-8")
    indexer = TranscriptionIndexer(MagicMock(), str(tmp_path), str(proc))
    assert indexer.index_metadata == {"indexed_files": {}, "last_update": None}


def test_check_updates_detects_new_and_modified_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    fresh = source / "transcripcion_new.md"
    old = source / "transcripcion_old.md"
    fresh.write_text("new", encoding="utf-8")
    old.write_text("old", encoding="utf-8")
    indexer = TranscriptionIndexer(MagicMock(), str(source), str(tmp_path / "proc"))
    indexer.index_metadata["indexed_files"][old.name] = {"mtime": old.stat().st_mtime + 100}
    assert set(indexer.check_updates()) == {fresh}
    indexer.index_metadata["indexed_files"][old.name]["mtime"] = 0
    assert set(indexer.check_updates()) == {fresh, old}


def test_index_transcription_updates_vector_store_and_metadata(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    original = source / "transcripcion_one.md"
    original.write_text("raw", encoding="utf-8")
    processed = tmp_path / "processed.md"
    processed.write_text("## Tema 1: Uno\n**⏱️ Timestamp**: 00:00:01\ntexto", encoding="utf-8")
    vector = MagicMock()
    indexer = TranscriptionIndexer(vector, str(source), str(tmp_path / "proc"))
    metadata = {"filename": original.name, "date": "2026-01-01", "time": "00:00:00"}
    indexer.loader.process_transcription = MagicMock(return_value=(processed, metadata))
    result = indexer.index_transcription(original)
    assert result["file"] == original.name and result["chunks"] == 1
    vector.add_documents.assert_called_once()
    assert original.name in indexer.index_metadata["indexed_files"]


def test_index_all_handles_empty_and_failures(tmp_path):
    vector = MagicMock()
    indexer = TranscriptionIndexer(vector, str(tmp_path), str(tmp_path / "proc"))
    indexer.loader.load_from_directory = MagicMock(return_value=[])
    assert indexer.index_all() == {"indexed": 0, "chunks": 0, "files": []}
    file_path = tmp_path / "transcripcion_bad.md"
    file_path.write_text("bad", encoding="utf-8")
    indexer.loader.load_from_directory.return_value = [file_path]
    indexer.index_transcription = MagicMock(side_effect=RuntimeError("bad file"))
    assert indexer.index_all() == {"indexed": 0, "chunks": 0, "files": []}


def test_index_new_handles_empty_and_success(tmp_path):
    indexer = TranscriptionIndexer(MagicMock(), str(tmp_path), str(tmp_path / "proc"))
    indexer.check_updates = MagicMock(return_value=[])
    assert indexer.index_new()["indexed"] == 0
    file_path = tmp_path / "transcripcion_new.md"
    file_path.write_text("new", encoding="utf-8")
    indexer.check_updates.return_value = [file_path]
    indexer.index_transcription = MagicMock(return_value={"file": file_path.name, "chunks": 2})
    result = indexer.index_new()
    assert result["indexed"] == 1 and result["chunks"] == 2


def test_get_indexed_files_sorts_by_date(tmp_path):
    indexer = TranscriptionIndexer(MagicMock(), str(tmp_path), str(tmp_path / "proc"))
    indexer.index_metadata["indexed_files"] = {
        "old.md": {"metadata": {"date": "2025-01-01"}, "chunks": 1, "indexed_at": "a", "processed_file": "p1"},
        "new.md": {"metadata": {"date": "2026-01-01"}, "chunks": 2, "indexed_at": "b", "processed_file": "p2"},
    }
    assert [item["filename"] for item in indexer.get_indexed_files()] == ["new.md", "old.md"]


def test_create_chunks_splits_long_and_untitled_sections():
    indexer = TranscriptionIndexer.__new__(TranscriptionIndexer)
    content = "## Tema 1: Largo\n" + ("palabra " * 11) + "\nTexto sin titulo"
    chunks = indexer._create_chunks(content, {"filename": "a.md", "date": "2026", "time": "00:00:00"}, chunk_size=5)
    assert len(chunks) >= 3
    assert all(item["metadata"]["word_count"] <= 5 for item in chunks)
