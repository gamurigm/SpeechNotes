import asyncio
import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks, HTTPException

_fake_dependencies = {}

_pydub = ModuleType("pydub")
_pydub.AudioSegment = MagicMock
_fake_dependencies["pydub"] = _pydub

_environment = ModuleType("src.core.environment_factory")
_environment.TranscriptionEnvironmentFactoryProvider = MagicMock()
_fake_dependencies["src.core.environment_factory"] = _environment

_transcription = ModuleType("src.transcription")
for _name in ("FormatterFactory", "OutputWriter", "TranscriptionService"):
    setattr(_transcription, _name, MagicMock)
_fake_dependencies["src.transcription"] = _transcription

_database = ModuleType("src.database")
_database.MongoManager = MagicMock
_fake_dependencies["src.database"] = _database

for _module_name, _class_name in (
    ("src.agent.transcription_ingestor", "TranscriptionIngestor"),
    ("src.agent.transcription_analyzer", "TranscriptionAnalyzer"),
    ("src.agent.document_generator", "DocumentGenerator"),
):
    _module = ModuleType(_module_name)
    setattr(_module, _class_name, MagicMock)
    _fake_dependencies[_module_name] = _module

_saved_modules = {name: sys.modules.get(name) for name in _fake_dependencies}
sys.modules.update(_fake_dependencies)
transcribe = importlib.import_module("backend.routers.transcribe")
for _name, _saved in _saved_modules.items():
    if _saved is None:
        sys.modules.pop(_name, None)
    else:
        sys.modules[_name] = _saved


class FakeUpload:
    def __init__(self, filename, chunks):
        self.filename = filename
        self._chunks = iter(chunks)

    async def read(self, _size=-1):
        return next(self._chunks, b"")


def test_process_audio_file_standardizes_and_exports(monkeypatch, tmp_path):
    audio = MagicMock()
    audio.set_frame_rate.return_value = audio
    audio.set_channels.return_value = audio
    audio.set_sample_width.return_value = audio
    from_file = MagicMock(return_value=audio)
    monkeypatch.setattr(transcribe.AudioSegment, "from_file", from_file, raising=False)
    source = tmp_path / "input.mp3"
    output = tmp_path / "output.wav"

    assert transcribe.process_audio_file(source, output) is True
    from_file.assert_called_once_with(str(source))
    audio.set_frame_rate.assert_called_once_with(16000)
    audio.set_channels.assert_called_once_with(1)
    audio.set_sample_width.assert_called_once_with(2)
    audio.export.assert_called_once_with(str(output), format="wav")


def test_process_audio_file_returns_false_on_conversion_error(monkeypatch, tmp_path):
    monkeypatch.setattr(
        transcribe.AudioSegment,
        "from_file",
        MagicMock(side_effect=RuntimeError("ffmpeg unavailable")),
        raising=False,
    )

    assert transcribe.process_audio_file(tmp_path / "in", tmp_path / "out") is False


def test_run_post_processing_invokes_all_steps(monkeypatch, tmp_path):
    ingestor = MagicMock()
    analyzer = MagicMock()
    generator = MagicMock()
    monkeypatch.setattr(transcribe, "TranscriptionIngestor", MagicMock(return_value=ingestor))
    monkeypatch.setattr(transcribe, "TranscriptionAnalyzer", MagicMock(return_value=analyzer))
    monkeypatch.setattr(transcribe, "DocumentGenerator", MagicMock(return_value=generator))
    markdown = tmp_path / "note.md"

    asyncio.run(transcribe.run_post_processing(markdown, "uploaded_file", "audio.wav"))

    ingestor._ingest_file.assert_called_once_with(
        markdown, source_type="uploaded_file", source_filename="audio.wav"
    )
    analyzer.analyze_pending.assert_called_once_with()
    generator.generate_all.assert_called_once_with()


def test_run_post_processing_contains_collaborator_errors(monkeypatch, tmp_path):
    failing = MagicMock()
    failing._ingest_file.side_effect = RuntimeError("database unavailable")
    monkeypatch.setattr(transcribe, "TranscriptionIngestor", MagicMock(return_value=failing))
    monkeypatch.setattr(transcribe.traceback, "print_exc", MagicMock())

    asyncio.run(transcribe.run_post_processing(tmp_path / "note.md"))

    transcribe.traceback.print_exc.assert_called_once_with()


def test_full_pipeline_stops_when_audio_conversion_fails(monkeypatch, tmp_path):
    temp_dir = tmp_path / "job"
    temp_dir.mkdir()
    monkeypatch.setattr(transcribe, "process_audio_file", MagicMock(return_value=False))

    asyncio.run(
        transcribe.full_transcription_pipeline(
            temp_dir / "upload.mp3", "output.md", temp_dir, "original.mp3"
        )
    )

    assert not temp_dir.exists()


def test_full_pipeline_transcribes_validates_and_post_processes(monkeypatch, tmp_path):
    temp_dir = tmp_path / "job"
    temp_dir.mkdir()
    source = temp_dir / "upload.mp3"
    generated = tmp_path / "notas" / "result.md"
    environment = MagicMock()
    transcriber = MagicMock()
    environment.create_transcriber.return_value = transcriber
    service = MagicMock()
    service.transcribe_audio_file.return_value = generated
    post_process = MagicMock()

    async def fake_post_process(*args, **kwargs):
        post_process(*args, **kwargs)

    monkeypatch.setattr(transcribe, "process_audio_file", MagicMock(return_value=True))
    monkeypatch.setattr(
        transcribe.TranscriptionEnvironmentFactoryProvider,
        "get_riva_live",
        MagicMock(return_value=environment),
    )
    monkeypatch.setattr(
        transcribe.FormatterFactory,
        "create",
        MagicMock(return_value="formatter"),
        raising=False,
    )
    monkeypatch.setattr(transcribe, "OutputWriter", MagicMock(return_value="writer"))
    monkeypatch.setattr(
        transcribe, "TranscriptionService", MagicMock(return_value=service)
    )
    monkeypatch.setattr(transcribe, "validate_path_within", MagicMock(return_value=generated))
    monkeypatch.setattr(transcribe, "run_post_processing", fake_post_process)

    asyncio.run(
        transcribe.full_transcription_pipeline(source, "output.md", temp_dir, "original.mp3")
    )

    service.transcribe_audio_file.assert_called_once_with(
        temp_dir / "processed.wav", output_file="output.md"
    )
    post_process.assert_called_once_with(
        generated, source_type="uploaded_file", source_filename="original.mp3"
    )
    assert not temp_dir.exists()


def test_full_pipeline_contains_runtime_and_cleanup_errors(monkeypatch, tmp_path):
    temp_dir = tmp_path / "job"
    temp_dir.mkdir()
    monkeypatch.setattr(transcribe, "process_audio_file", MagicMock(side_effect=RuntimeError("boom")))
    monkeypatch.setattr(transcribe.traceback, "print_exc", MagicMock())
    monkeypatch.setattr(transcribe.shutil, "rmtree", MagicMock(side_effect=OSError("locked")))

    asyncio.run(
        transcribe.full_transcription_pipeline(temp_dir / "in", "out.md", temp_dir)
    )

    transcribe.traceback.print_exc.assert_called_once_with()


def test_upload_saves_chunks_and_schedules_pipeline(monkeypatch, tmp_path):
    temp_dir = tmp_path / "upload"
    temp_dir.mkdir()
    tasks = BackgroundTasks()
    monkeypatch.setattr(transcribe.tempfile, "mkdtemp", MagicMock(return_value=str(temp_dir)))
    monkeypatch.setattr(
        transcribe.uuid, "uuid4", MagicMock(return_value=SimpleNamespace(hex="abc123"))
    )

    result = asyncio.run(
        transcribe.transcribe_uploaded_file(
            tasks, FakeUpload("../unsafe name.MP3", [b"first", b"second", b""])
        )
    )

    saved = temp_dir / "upload_abc123.mp3"
    assert saved.read_bytes() == b"firstsecond"
    assert result["status"] == "success"
    assert result["original_filename"] == "unsafe name.MP3"
    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].func is transcribe.full_transcription_pipeline
    assert tasks.tasks[0].args[0] == saved


def test_upload_uses_safe_fallback_extension(monkeypatch, tmp_path):
    temp_dir = tmp_path / "upload"
    temp_dir.mkdir()
    tasks = BackgroundTasks()
    monkeypatch.setattr(transcribe.tempfile, "mkdtemp", MagicMock(return_value=str(temp_dir)))
    monkeypatch.setattr(
        transcribe.uuid, "uuid4", MagicMock(return_value=SimpleNamespace(hex="id"))
    )

    result = asyncio.run(
        transcribe.transcribe_uploaded_file(tasks, FakeUpload("payload.exe", [b"data", b""]))
    )

    assert (temp_dir / "upload_id.audio").read_bytes() == b"data"
    assert result["original_filename"] == "payload.exe"


def test_upload_failure_cleans_temp_directory(monkeypatch, tmp_path):
    temp_dir = tmp_path / "upload"
    temp_dir.mkdir()
    monkeypatch.setattr(transcribe.tempfile, "mkdtemp", MagicMock(return_value=str(temp_dir)))
    monkeypatch.setattr(
        transcribe.aiofiles,
        "open",
        MagicMock(side_effect=OSError("disk full")),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            transcribe.transcribe_uploaded_file(
                BackgroundTasks(), FakeUpload("audio.wav", [b"data"])
            )
        )

    assert exc.value.status_code == 500
    assert "disk full" in exc.value.detail
    assert not temp_dir.exists()
