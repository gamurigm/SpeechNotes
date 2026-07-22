import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure optional imports are mocked if missing
for mod in ["logfire", "pymongo", "pymongo.errors"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

if isinstance(sys.modules.get("logfire"), MagicMock):
    sys.modules["logfire"].instrument = lambda f=None: (f if f else lambda x: x)

from src.agent.transcription_ingestor import TranscriptionIngestor


def test_initial_segmentation_splits_by_timestamp():
    ingestor = TranscriptionIngestor.__new__(TranscriptionIngestor)
    content = "**00:00:00** Primer segmento\n**00:05:00** Segundo segmento"
    
    segments = ingestor._initial_segmentation(content, "trans_123")
    assert len(segments) == 2
    assert segments[0]["timestamp"] == "00:00:00"
    assert segments[0]["content"] == "Primer segmento"
    assert segments[1]["timestamp"] == "00:05:00"
    assert segments[1]["content"] == "Segundo segmento"


def test_extract_metadata_calculates_words(tmp_path):
    ingestor = TranscriptionIngestor.__new__(TranscriptionIngestor)
    file_path = tmp_path / "transcripcion_20260722_090000.md"
    file_path.write_text("uno dos tres cuatro cinco", encoding="utf-8")
    
    metadata = ingestor._extract_metadata(file_path)
    assert metadata["date"] == "2026-07-22"
    assert metadata["time"] == "09:00:00"
    assert metadata["word_count"] == 5


def test_ingest_file_skips_existing():
    ingestor = TranscriptionIngestor.__new__(TranscriptionIngestor)
    mock_db = MagicMock()
    mock_db.transcriptions.find_one.return_value = {"_id": "exists"}
    ingestor.db = mock_db
    
    dummy_path = Path("transcripcion_test.md")
    result = ingestor._ingest_file(dummy_path)
    assert result is False


def test_ingest_all_adds_skips_and_counts_errors(tmp_path):
    (tmp_path / "transcripcion_20260722_090000.md").write_text("**00:00:00** hola", encoding="utf-8")
    (tmp_path / "mi_audio_20260722_100000.md").write_text("texto", encoding="utf-8")
    ingestor = TranscriptionIngestor.__new__(TranscriptionIngestor)
    ingestor.source_dir = tmp_path
    ingestor._ingest_file = MagicMock(side_effect=[True, False])
    assert ingestor.ingest_all() == {"added": 1, "skipped": 1, "errors": 0}
    ingestor._ingest_file = MagicMock(side_effect=RuntimeError("broken"))
    assert ingestor.ingest_all()["errors"] == 2


def test_ingest_all_missing_directory_raises(tmp_path):
    ingestor = TranscriptionIngestor.__new__(TranscriptionIngestor)
    ingestor.source_dir = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        ingestor.ingest_all()


def test_ingest_file_success_inserts_document_and_segments(tmp_path):
    file_path = tmp_path / "upload.md"
    file_path.write_text("texto inicial\n**00:02:00** segundo", encoding="utf-8")
    ingestor = TranscriptionIngestor.__new__(TranscriptionIngestor)
    ingestor.db = MagicMock()
    ingestor.db.transcriptions.find_one.return_value = None
    ingestor.db.transcriptions.insert_one.return_value = MagicMock(inserted_id="new-id")
    assert ingestor._ingest_file(str(file_path), "uploaded_file", "original.wav") is True
    inserted = ingestor.db.transcriptions.insert_one.call_args.args[0]
    assert inserted["source_filename"] == "original.wav" and inserted["source_type"] == "uploaded_file"
    ingestor.db.segments.insert_many.assert_called_once()


def test_initial_segmentation_handles_prefix_and_empty_content():
    ingestor = TranscriptionIngestor.__new__(TranscriptionIngestor)
    segments = ingestor._initial_segmentation("prefijo **00:01:00** texto", "id")
    assert [item["sequence"] for item in segments] == [1, 2]
    assert ingestor._initial_segmentation("", "id") == []
