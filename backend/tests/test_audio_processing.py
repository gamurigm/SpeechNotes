import asyncio
import importlib
import sys
from types import ModuleType
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

_audio_name = "backend.services.audio"
_pipeline_name = "backend.services.audio.pipeline"
_saved_modules = {name: sys.modules.get(name) for name in (_audio_name, _pipeline_name)}
_audio_module = ModuleType(_audio_name)
for _name in ("ASRRequest", "NoiseRemovalRequest"):
    setattr(_audio_module, _name, MagicMock)
for _name in ("ASRService", "NoiseRemovalService"):
    setattr(_audio_module, _name, MagicMock)
_pipeline_module = ModuleType(_pipeline_name)
_pipeline_module.PipelineContext = MagicMock
_pipeline_module.PipelineFactory = MagicMock()
sys.modules[_audio_name] = _audio_module
sys.modules[_pipeline_name] = _pipeline_module
audio_router = importlib.import_module("backend.routers.audio_processing")
for _name, _saved in _saved_modules.items():
    if _saved is None:
        sys.modules.pop(_name, None)
    else:
        sys.modules[_name] = _saved


class FakeUpload:
    def __init__(self, content):
        self.content = content

    async def read(self):
        return self.content


def test_transcribe_audio_rejects_empty_upload():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(audio_router.transcribe_audio(FakeUpload(b"")))
    assert exc.value.status_code == 400


def test_transcribe_audio_returns_service_result(monkeypatch):
    service = MagicMock()
    service.transcribe = AsyncMock(
        return_value=SimpleNamespace(
            text="hello", language="en", confidence=0.9, duration_seconds=2.5
        )
    )
    request_cls = MagicMock(return_value="request")
    monkeypatch.setattr(audio_router, "ASRService", MagicMock(return_value=service))
    monkeypatch.setattr(audio_router, "ASRRequest", request_cls)

    result = asyncio.run(audio_router.transcribe_audio(FakeUpload(b"audio"), "es", "en"))

    assert result == {
        "text": "hello",
        "language": "en",
        "confidence": 0.9,
        "duration_seconds": 2.5,
    }
    request_cls.assert_called_once_with(audio_bytes=b"audio", language="es", translate_to="en")
    service.transcribe.assert_awaited_once_with("request")


def test_denoise_audio_rejects_empty_upload():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(audio_router.denoise_audio(FakeUpload(b"")))
    assert exc.value.status_code == 400


def test_denoise_audio_builds_wav_response(monkeypatch):
    service = MagicMock()
    service.denoise = AsyncMock(
        return_value=SimpleNamespace(
            audio_bytes=b"clean", enhancement_applied="enhanced", sample_rate=16000
        )
    )
    request_cls = MagicMock(return_value="request")
    monkeypatch.setattr(audio_router, "NoiseRemovalService", MagicMock(return_value=service))
    monkeypatch.setattr(audio_router, "NoiseRemovalRequest", request_cls)

    response = asyncio.run(audio_router.denoise_audio(FakeUpload(b"noisy"), 8000))

    assert response.body == b"clean"
    assert response.media_type == "audio/wav"
    assert response.headers["x-bnr-mode"] == "enhanced"
    assert response.headers["x-sample-rate"] == "16000"
    request_cls.assert_called_once_with(audio_bytes=b"noisy", sample_rate=8000)


def test_pipeline_rejects_empty_upload():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(audio_router.run_pipeline(FakeUpload(b"")))
    assert exc.value.status_code == 400


def test_pipeline_converts_unknown_variant_to_http_400(monkeypatch):
    monkeypatch.setattr(
        audio_router.PipelineFactory, "create", MagicMock(side_effect=ValueError("unknown pipeline"))
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(audio_router.run_pipeline(FakeUpload(b"audio"), pipeline="invalid"))
    assert exc.value.status_code == 400
    assert exc.value.detail == "unknown pipeline"


def test_pipeline_returns_processing_summary(monkeypatch):
    processed = SimpleNamespace(
        transcript="hola",
        translated_text="hello",
        detected_language="es",
        errors=[],
        cleaned_audio=b"clean",
    )
    pipeline = MagicMock()
    pipeline.run = AsyncMock(return_value=processed)
    context_cls = MagicMock(return_value="context")
    monkeypatch.setattr(audio_router.PipelineFactory, "create", MagicMock(return_value=pipeline))
    monkeypatch.setattr(audio_router, "PipelineContext", context_cls)

    result = asyncio.run(
        audio_router.run_pipeline(FakeUpload(b"audio"), "full", "es", "en", 44100)
    )

    assert result == {
        "pipeline": "full",
        "transcript": "hola",
        "translated_text": "hello",
        "detected_language": "es",
        "errors": [],
        "bnr_applied": True,
    }
    context_cls.assert_called_once_with(
        audio_bytes=b"audio", sample_rate=44100, language_hint="es", translate_to="en"
    )
    pipeline.run.assert_awaited_once_with("context")
