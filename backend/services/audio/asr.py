"""Application service for audio transcription through the configured NIM."""

from __future__ import annotations

import io
import logging
import wave
from dataclasses import dataclass

from backend.services.nim.registry import NIMRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ASRRequest:
    """Input accepted by both file and realtime transcription flows."""

    audio_bytes: bytes
    sample_rate: int = 16000
    language: str | None = None
    translate_to: str | None = None
    diarize: bool = False


@dataclass(frozen=True)
class ASRResult:
    """Stable application result independent of the selected NIM client."""

    text: str
    language: str | None
    confidence: float
    duration_seconds: float


class ASRService:
    """Resolve the correct ASR client and normalize its response."""

    def __init__(self, registry: NIMRegistry | None = None) -> None:
        self._registry = registry or NIMRegistry.instance()

    async def transcribe(self, request: ASRRequest) -> ASRResult:
        if not request.audio_bytes:
            raise ValueError("Audio data is empty")

        client = self._registry.get_asr(request.language)
        result = await client.transcribe(
            request.audio_bytes,
            sample_rate=request.sample_rate,
            language=request.language,
        )
        if self._should_try_whisper(request.language, result.confidence):
            logger.warning(
                "[ASR] Spanish provider failed; retrying the same audio with Whisper"
            )
            whisper = self._registry.get("asr")
            result = await whisper.transcribe(
                request.audio_bytes,
                sample_rate=request.sample_rate,
                language=request.language,
            )
        return ASRResult(
            text=result.text,
            language=result.language or request.language,
            confidence=result.confidence,
            duration_seconds=_wav_duration(request.audio_bytes, request.sample_rate),
        )

    @staticmethod
    def _should_try_whisper(language: str | None, confidence: float) -> bool:
        """Use Whisper only when the Spanish provider reports an actual failure."""
        return bool(language and language.lower().startswith("es") and confidence <= 0)


def _wav_duration(audio_bytes: bytes, fallback_sample_rate: int) -> float:
    """Return WAV duration when possible without rejecting raw PCM callers."""
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            return wav_file.getnframes() / frame_rate if frame_rate else 0.0
    except (EOFError, wave.Error):
        bytes_per_second = max(fallback_sample_rate, 1) * 2
        return len(audio_bytes) / bytes_per_second
