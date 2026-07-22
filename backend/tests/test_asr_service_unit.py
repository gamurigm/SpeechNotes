import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.audio.asr import ASRRequest, ASRService
from backend.services.nim.protocols import TranscriptionResult


def _client(text: str, confidence: float = 1.0):
    client = MagicMock()
    client.transcribe = AsyncMock(
        return_value=TranscriptionResult(
            text=text,
            language="es",
            confidence=confidence,
        )
    )
    return client


def test_transcribe_rejects_empty_audio():
    with pytest.raises(ValueError, match="empty"):
        asyncio.run(ASRService(MagicMock()).transcribe(ASRRequest(audio_bytes=b"")))


def test_transcribe_returns_primary_result_without_fallback():
    registry = MagicMock()
    primary = _client("Texto principal")
    registry.get_asr.return_value = primary

    result = asyncio.run(
        ASRService(registry).transcribe(ASRRequest(audio_bytes=b"pcm", language="es"))
    )

    assert result.text == "Texto principal"
    registry.get.assert_not_called()


def test_transcribe_falls_back_to_whisper_after_spanish_provider_failure():
    registry = MagicMock()
    registry.get_asr.return_value = _client("", confidence=0.0)
    whisper = _client("Texto recuperado")
    registry.get.return_value = whisper

    result = asyncio.run(
        ASRService(registry).transcribe(ASRRequest(audio_bytes=b"pcm", language="es"))
    )

    assert result.text == "Texto recuperado"
    registry.get.assert_called_once_with("asr")
    whisper.transcribe.assert_awaited_once_with(
        b"pcm",
        sample_rate=16000,
        language="es",
    )


def test_transcribe_does_not_fallback_for_successful_silence_or_other_languages():
    registry = MagicMock()
    registry.get_asr.side_effect = [
        _client("", confidence=1.0),
        _client("", confidence=0.0),
    ]
    service = ASRService(registry)

    spanish = asyncio.run(service.transcribe(ASRRequest(audio_bytes=b"pcm", language="es")))
    english = asyncio.run(service.transcribe(ASRRequest(audio_bytes=b"pcm", language="en")))

    assert spanish.text == ""
    assert english.text == ""
    registry.get.assert_not_called()
