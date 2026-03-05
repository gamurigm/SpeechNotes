"""
Groq Whisper ASR Client — Infrastructure Layer

Concrete adapter for Groq's Whisper Large V3 Turbo endpoint.

NVIDIA Parakeet NIM was retired from the cloud API, so this client
provides a drop-in replacement using Groq's ultra-fast Whisper
implementation.  It implements the same AudioTranscriptionPort so the
rest of the application is unaware of the provider swap (OCP / DIP).

Design Patterns:
    - Adapter (Structural): Wraps the groq Python SDK behind the
      AudioTranscriptionPort so callers never import groq directly.
    - Strategy (Behavioral): Swappable with any other ASR adapter
      registered in NIMRegistry.

Architecture Layer: Infrastructure
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from groq import AsyncGroq

from backend.services.nim.protocols import (
    AudioTranscriptionPort,
    NIMConfig,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class GroqASRClient(AudioTranscriptionPort):
    """
    Adapter around AsyncGroq that provides speech-to-text via
    Whisper Large V3 Turbo hosted on Groq's inference infrastructure.

    Groq offers free-tier access with generous rate limits, making it
    an excellent replacement for NVIDIA Parakeet NIM.

    Supported models:
        - whisper-large-v3-turbo  (default, fastest)
        - whisper-large-v3        (higher accuracy)
        - distil-whisper-large-v3-en  (English-only, fastest)
    """

    def __init__(self, config: NIMConfig) -> None:
        self._cfg = config
        self._client = AsyncGroq(api_key=config.api_key)
        logger.info(
            "[Groq:ASR] Initialized client '%s' → model='%s'",
            config.name,
            config.model_id,
        )

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio using Groq Whisper.

        Args:
            audio_bytes: WAV (PCM 16-bit, 16kHz, mono) bytes.
            sample_rate: Source sample rate (informational).
            language:    BCP-47 language hint e.g. "en", "es".
        """
        transcription = await self._client.audio.transcriptions.create(
            file=("audio.wav", io.BytesIO(audio_bytes)),
            model=self._cfg.model_id,
            language=language or "",
            response_format="text",
        )

        # response_format="text" returns the raw string
        text = str(transcription).strip() if transcription else ""

        return TranscriptionResult(
            text=text,
            language=language,
            confidence=1.0,
        )
