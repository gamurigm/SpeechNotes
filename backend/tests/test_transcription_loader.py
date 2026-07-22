import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure optional imports are mocked if missing
if "dotenv" not in sys.modules:
    sys.modules["dotenv"] = MagicMock()

from src.agent.transcription_loader import TranscriptionLoader


def test_extract_metadata_with_timestamp_filename(tmp_path):
    file_path = tmp_path / "transcripcion_20260722_120000.md"
    file_path.write_text("**00:00:00** Hola clase de prueba con diez palabras en total.", encoding="utf-8")
    
    loader = TranscriptionLoader(source_dir=str(tmp_path), processed_dir=str(tmp_path / "out"))
    metadata = loader.extract_metadata(file_path)
    
    assert metadata["date"] == "2026-07-22"
    assert metadata["time"] == "12:00:00"
    assert metadata["word_count"] > 0
    assert metadata["segment_count"] == 1


def test_parse_topic_response_valid_structure():
    loader = TranscriptionLoader()
    response = """TEMA: Introducción a la IA
TIMESTAMP: 00:00:00
PUNTOS:
- Conceptos básicos
- Algoritmos principales
---
TEMA: Redes Neuronales
TIMESTAMP: 00:15:00
PUNTOS:
- Perceptrón
- Backpropagation"""

    topics = loader._parse_topic_response(response, "")
    assert len(topics) == 2
    assert topics[0]["title"] == "Introducción a la IA"
    assert topics[0]["timestamp_start"] == "00:00:00"
    assert topics[0]["key_points"] == ["Conceptos básicos", "Algoritmos principales"]
    assert topics[1]["title"] == "Redes Neuronales"


def test_fallback_segmentation_with_timestamps():
    loader = TranscriptionLoader()
    content = "**00:00:00** Inicio de clase\n**00:10:00** Segunda parte de la clase"
    
    topics = loader._fallback_segmentation(content)
    assert len(topics) >= 1
    assert topics[0]["timestamp_start"] == "00:00:00"


def test_save_processed_creates_file(tmp_path):
    out_dir = tmp_path / "processed"
    loader = TranscriptionLoader(source_dir=str(tmp_path), processed_dir=str(out_dir))
    
    saved_path = loader.save_processed("# Content", "transcripcion_123.md")
    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8") == "# Content"
