"""Isolated unit tests for audio-format orchestration paths."""

import asyncio
import sys
from types import ModuleType
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from types import SimpleNamespace
import pytest


# The production formatter depends on pydub/FFmpeg. Router orchestration only
# needs its public service contract, so keep this unit test independent of the
# optional media stack.
service_module = ModuleType("services.audio.audio_formatter")
service_module.AudioFormatterService = MagicMock(return_value=MagicMock())
services_package = ModuleType("services")
services_package.__path__ = []
audio_package = ModuleType("services.audio")
audio_package.__path__ = []
sys.modules.setdefault("services", services_package)
sys.modules.setdefault("services.audio", audio_package)
sys.modules.setdefault("services.audio.audio_formatter", service_module)

import backend.routers.audio_format as module
for _name in ("services.audio.audio_formatter", "services.audio", "services"):
    sys.modules.pop(_name, None)


class FakeTask:
    def __init__(self):
        self.callback = None

    def add_done_callback(self, callback):
        self.callback = callback


def test_batch_convert_stores_background_task_and_returns_job(tmp_path, monkeypatch):
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"RIFF")
    formatter = MagicMock()
    formatter.create_job.return_value = "job-123"
    monkeypatch.setattr(module, "audio_formatter", formatter)
    monkeypatch.setattr(module, "project_root", tmp_path)

    fake_task = FakeTask()

    def create_task(coroutine):
        coroutine.close()
        return fake_task

    monkeypatch.setattr(module.asyncio, "create_task", create_task)
    module.background_tasks.clear()
    request = module.BatchConvertRequest(
        files=["sample.wav"], output_format="mp3", profile="podcast", max_concurrent=2
    )
    response = asyncio.run(module.batch_convert_files(request, api_ok=True))
    assert response == module.JobResponse(job_id="job-123", total_files=1, status="processing", ws_url="/ws/job-123")
    formatter.create_job.assert_called_once_with(files=["sample.wav"], output_format="mp3", profile="podcast")
    assert fake_task in module.background_tasks
    assert fake_task.callback == module.background_tasks.discard
    module.background_tasks.clear()


def test_resolve_project_path_rejects_escape(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "project_root", tmp_path)
    with pytest.raises(module.HTTPException) as exc:
        module.resolve_project_path("../outside.wav")
    assert exc.value.status_code == 400


@pytest.mark.parametrize("endpoint", [module.get_available_profiles, module.cleanup_temp_files])
def test_simple_service_endpoints(endpoint, monkeypatch):
    service = MagicMock()
    service.get_available_profiles.return_value = [{"name": "x", "description": "d", "settings": {}}]
    monkeypatch.setattr(module, "audio_formatter", service)
    result = asyncio.run(endpoint(True))
    assert result == ([{"name": "x", "description": "d", "settings": {}}] if endpoint is module.get_available_profiles else {"status": "success", "message": "Temporary files cleaned up"})


def test_detect_and_convert_success(tmp_path, monkeypatch):
    path = tmp_path / "ok.wav"
    path.write_bytes(b"audio")
    monkeypatch.setattr(module, "project_root", tmp_path)
    metadata = SimpleNamespace(format="wav", codec="pcm", sample_rate=16000, channels=1,
                               bit_depth=16, duration_seconds=1.2, file_size_mb=0.1,
                               is_optimized=True, is_transcription_ready=True)
    result = SimpleNamespace(status="completed", error_message=None, to_dict=lambda: {"ok": True})
    service = MagicMock()
    service.detect_format.return_value = metadata
    service.convert_file = AsyncMock(return_value=result)
    monkeypatch.setattr(module, "audio_formatter", service)
    detected = asyncio.run(module.detect_audio_format(module.DetectFormatRequest(file_path="ok.wav"), True))
    converted = asyncio.run(module.convert_single_file(module.ConvertFileRequest(input_path="ok.wav"), True))
    assert detected.format == "wav" and detected.is_transcription_ready
    assert converted == {"ok": True}


def test_convert_failed_and_job_status(tmp_path, monkeypatch):
    path = tmp_path / "ok.wav"
    path.write_bytes(b"audio")
    monkeypatch.setattr(module, "project_root", tmp_path)
    service = MagicMock()
    service.convert_file = AsyncMock(return_value=SimpleNamespace(status="failed", error_message="bad"))
    job = SimpleNamespace(job_id="j", status="done", total_files=1, successful=1, failed=0,
                          created_at=datetime(2026, 1, 1), completed_at=None, results=[])
    service.get_job.side_effect = [None, job]
    monkeypatch.setattr(module, "audio_formatter", service)
    with pytest.raises(module.HTTPException) as exc:
        asyncio.run(module.convert_single_file(module.ConvertFileRequest(input_path="ok.wav"), True))
    assert exc.value.status_code == 500
    with pytest.raises(module.HTTPException) as exc:
        asyncio.run(module.get_job_status("missing", True))
    assert exc.value.status_code == 404
    status = asyncio.run(module.get_job_status("j", True))
    assert status["job_id"] == "j" and status["completed_at"] is None


def test_download_and_batch_missing_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "project_root", tmp_path)
    with pytest.raises(module.HTTPException) as exc:
        asyncio.run(module.download_formatted_file("missing.wav", True))
    assert exc.value.status_code == 404
    with pytest.raises(module.HTTPException) as exc:
        asyncio.run(module.batch_convert_files(module.BatchConvertRequest(files=["missing.wav"]), True))
    assert exc.value.status_code == 404


def test_audio_processing_operations(tmp_path, monkeypatch):
    path = tmp_path / "clip.wav"
    path.write_bytes(b"audio")
    monkeypatch.setattr(module, "project_root", tmp_path)
    result = SimpleNamespace(status="completed", error_message=None, to_dict=lambda: {"ok": True})
    service = MagicMock()
    for name in ("normalize_audio", "trim_silence", "extract_segment", "merge_files", "change_speed"):
        setattr(service, name, AsyncMock(return_value=result))
    monkeypatch.setattr(module, "audio_formatter", service)
    assert asyncio.run(module.normalize_audio_volume(True, "clip.wav", -16)) == {"ok": True}
    assert asyncio.run(module.trim_audio_silence(True, "clip.wav", -40)) == {"ok": True}
    assert asyncio.run(module.extract_audio_segment(True, "clip.wav", 0, 1)) == {"ok": True}
    assert asyncio.run(module.merge_audio_files(True, ["clip.wav"], "joined.wav")) == {"ok": True}
    assert asyncio.run(module.change_audio_speed(True, "clip.wav", 1.25)) == {"ok": True}
    service.normalize_audio.assert_awaited_once()
    service.merge_files.assert_awaited_once()
