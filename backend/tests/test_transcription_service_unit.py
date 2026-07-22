from datetime import datetime
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import MagicMock

if "src.core.riva_client" not in sys.modules:
    riva_stub = ModuleType("src.core.riva_client")
    riva_stub.RivaTranscriber = type("RivaTranscriber", (), {})
    sys.modules["src.core.riva_client"] = riva_stub
if "src.audio.capture" not in sys.modules:
    audio_stub = ModuleType("src.audio.capture")
    audio_stub.AudioRecorder = type("AudioRecorder", (), {})
    sys.modules["src.audio.capture"] = audio_stub

from src.transcription.service import TranscriptionService


def _service():
    transcriber = MagicMock()
    transcriber.offline_transcribe.return_value = "texto transcrito"
    formatter = MagicMock()
    formatter.format.return_value = "texto formateado"
    formatter.get_file_extension.return_value = ".md"
    writer = MagicMock()
    writer.write.return_value = Path("salida.md")
    return TranscriptionService(transcriber, formatter, writer), transcriber, formatter, writer


def test_transcribe_audio_file_orchestrates_dependencies(tmp_path):
    audio = tmp_path / "clase.wav"
    audio.write_bytes(b"audio")
    service, transcriber, formatter, writer = _service()

    assert service.transcribe_audio_file(audio, "en", "resultado") == Path("salida.md")
    transcriber.offline_transcribe.assert_called_once_with(b"audio", "en")
    metadata = formatter.format.call_args.args[1]
    assert metadata["audio_file"] == "clase.wav"
    assert metadata["language"] == "en"
    assert metadata["title"] == "Transcripción: clase.wav"
    writer.write.assert_called_once_with("texto formateado", "resultado", ".md")


def test_transcribe_recording_uses_given_start_and_duration():
    service, transcriber, formatter, writer = _service()
    recorder = MagicMock()
    recorder.record.return_value = b"recorded"
    started = datetime(2026, 7, 22, 9, 30)

    assert service.transcribe_recording(recorder, "es", "grabacion", started, 12.5) == Path("salida.md")
    transcriber.offline_transcribe.assert_called_once_with(b"recorded", "es")
    metadata = formatter.format.call_args.args[1]
    assert metadata["timestamp"] == started
    assert metadata["duration_seconds"] == 12.5
    assert metadata["audio_file"] == "recording.wav"
    writer.write.assert_called_once_with("texto formateado", "grabacion", ".md")


def test_transcribe_recording_uses_current_time_when_omitted():
    service, _, formatter, _ = _service()
    recorder = MagicMock()
    recorder.record.return_value = b"recorded"
    before = datetime.now()
    service.transcribe_recording(recorder)
    after = datetime.now()
    assert before <= formatter.format.call_args.args[1]["timestamp"] <= after


def test_transcribe_segments_formats_and_writes():
    service, _, formatter, writer = _service()
    segments = [(datetime(2026, 7, 22), "hola")]
    assert service.transcribe_segments(segments, "segmentos", "Silence") == Path("salida.md")
    formatter.format.assert_called_once_with(
        segments, {"title": "Transcripción por Segmentos", "method": "Silence"}
    )
    writer.write.assert_called_once_with("texto formateado", "segmentos", ".md")
