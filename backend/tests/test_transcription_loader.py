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


def test_load_directory_missing_raises(tmp_path):
    loader = TranscriptionLoader(str(tmp_path / "missing"), str(tmp_path / "out"))
    with pytest.raises(FileNotFoundError):
        loader.load_from_directory()


def test_extract_metadata_fallbacks_and_bracket_timestamps(tmp_path):
    file_path = tmp_path / "audio.md"
    file_path.write_text("[00:01:02] uno dos", encoding="utf-8")
    loader = TranscriptionLoader(str(tmp_path), str(tmp_path / "out"))
    metadata = loader.extract_metadata(file_path)
    assert metadata["segment_count"] == 1 and metadata["word_count"] == 3
    invalid = tmp_path / "transcripcion_20261399_999999.md"
    invalid.write_text("sin marcas", encoding="utf-8")
    fallback = loader.extract_metadata(invalid)
    assert fallback["segment_count"] == 1


def test_detect_topics_success_and_fallback(monkeypatch):
    loader = TranscriptionLoader()
    client = MagicMock()
    client.generate.return_value = "TEMA: Ciencia\nTIMESTAMP: 00:00:00\nPUNTOS:\n- dato"
    monkeypatch.setattr("src.llm.nvidia_client.NvidiaInferenceClient", lambda: client)
    topics = loader.detect_topics("contenido")
    assert topics[0]["title"] == "Ciencia"
    client.generate.side_effect = RuntimeError("offline")
    assert loader.detect_topics("**00:00:00** contenido")[0]["timestamp_start"] == "00:00:00"


def test_segment_by_topics_handles_existing_and_missing_matches():
    loader = TranscriptionLoader()
    existing = [{"timestamp_start": "00:00:00", "content": "ya"}]
    assert loader.segment_by_topics("texto", existing) is existing
    topics = [{"timestamp_start": "00:00:00", "content": ""}, {"timestamp_start": "00:01:00", "content": ""}]
    result = loader.segment_by_topics("00:00:00 primero\n00:01:00 segundo", topics)
    assert "primero" in result[0]["content"] and "segundo" in result[1]["content"]


def test_format_professional_markdown_includes_points(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    loader = TranscriptionLoader(str(tmp_path), str(tmp_path / "out"))
    source = tmp_path / "transcripcion_20260722_120000.md"
    source.write_text("texto", encoding="utf-8")
    result = loader.format_professional_md(
        {"date": "2026-07-22", "time": "12:00:00", "word_count": 4},
        [{"title": "Tema Uno", "timestamp_start": "00:00:00", "content": "texto", "key_points": ["punto"]}], source,
    )
    assert "Tabla de Contenidos" in result and "✓ punto" in result


def test_process_transcription_and_recent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    file_path = source / "transcripcion_20260722_120000.md"
    file_path.write_text("**00:00:00** hola", encoding="utf-8")
    loader = TranscriptionLoader(str(source), str(tmp_path / "out"))
    monkeypatch.setattr(loader, "detect_topics", lambda content: loader._fallback_segmentation(content))
    output, metadata = loader.process_transcription(file_path)
    assert output.exists() and metadata["word_count"] > 0
    assert loader.get_recent(1) == [file_path]
