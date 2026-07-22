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
