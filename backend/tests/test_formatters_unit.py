from datetime import datetime, timedelta
import sys
from types import ModuleType

import pytest

# Importing the transcription package also exposes TranscriptionService.  Its
# Riva type is irrelevant to formatter tests and the proprietary SDK is not
# installed in the lightweight local test environment.
if "src.core.riva_client" not in sys.modules:
    riva_stub = ModuleType("src.core.riva_client")
    riva_stub.RivaTranscriber = type("RivaTranscriber", (), {})
    sys.modules["src.core.riva_client"] = riva_stub
if "src.audio.capture" not in sys.modules:
    audio_stub = ModuleType("src.audio.capture")
    audio_stub.AudioRecorder = type("AudioRecorder", (), {})
    sys.modules["src.audio.capture"] = audio_stub

from src.transcription.formatters import (
    FormatterFactory,
    MarkdownFormatter,
    OutputWriter,
    PlainTextFormatter,
    SegmentedMarkdownFormatter,
)


def test_markdown_formatter_includes_metadata_and_counts():
    formatter = MarkdownFormatter()
    result = formatter.format("hola mundo", {
        "timestamp": datetime(2026, 7, 22, 10, 11, 12),
        "duration_seconds": 125,
        "title": "Clase",
        "audio_file": "clase.wav",
        "language": "es",
    })
    assert "# Clase" in result
    assert "2026-07-22 10:11:12" in result
    assert "2m 5s" in result
    assert "~2" in result and "clase.wav" in result
    assert formatter.get_file_extension() == ".md"


def test_markdown_formatter_uses_defaults():
    assert "Transcripción de Audio" in MarkdownFormatter().format("texto", {})


def test_segmented_markdown_empty_and_populated():
    formatter = SegmentedMarkdownFormatter()
    assert formatter.format([], {}) == ""
    start = datetime(2026, 7, 22, 8, 0, 0)
    result = formatter.format(
        [(start, "primero"), (start + timedelta(seconds=65), "segundo")],
        {"title": "Sesión", "method": "VAD"},
    )
    assert "# Sesión" in result
    assert "1m 5s" in result
    assert "primero segundo" in result
    assert "**[08:00:00]** primero" in result
    assert "VAD" in result
    assert formatter.get_file_extension() == ".md"


def test_plain_text_formatter():
    formatter = PlainTextFormatter()
    result = formatter.format("contenido", {"timestamp": datetime(2026, 1, 2, 3, 4, 5)})
    assert result == "[2026-01-02 03:04:05]\n\ncontenido\n"
    assert formatter.get_file_extension() == ".txt"
    assert "texto" in formatter.format("texto", {})


def test_output_writer_explicit_auto_extension_and_safe_name(tmp_path):
    writer = OutputWriter(tmp_path)
    path = writer.write("áé", "nota", ".txt")
    assert path.name == "nota.txt"
    assert path.read_text(encoding="utf-8-sig") == "áé"

    safe_path = writer.write("seguro", "../fuera.md", ".md")
    assert safe_path.parent == tmp_path
    assert safe_path.exists()


def test_output_writer_auto_generates_name(tmp_path):
    path = OutputWriter(tmp_path).write("contenido", extension=".md")
    assert path.name.startswith("transcripcion_")
    assert path.suffix == ".md"


@pytest.mark.parametrize("kind, expected", [
    ("markdown", MarkdownFormatter),
    ("segmented_markdown", SegmentedMarkdownFormatter),
    ("plain", PlainTextFormatter),
])
def test_formatter_factory_supported(kind, expected):
    assert isinstance(FormatterFactory.create(kind), expected)


def test_formatter_factory_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown format type"):
        FormatterFactory.create("pdf")
