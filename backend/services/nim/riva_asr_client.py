"""
Riva ASR Client — Infrastructure Layer

Concrete adapter for NVIDIA Riva ASR endpoints
hosted on NVIDIA Cloud Functions (NVCF) via gRPC.

This client uses the official ``nvidia-riva-client`` SDK to call
the Riva ASR service on ``grpc.nvcf.nvidia.com:443``, authenticating
with an NVIDIA API key and routing to the selected NVCF function via
the ``function-id`` gRPC metadata header.

Design Patterns:
    - Adapter (Structural): Wraps the Riva gRPC SDK behind the
      ``AudioTranscriptionPort`` so callers never import riva.client
      directly.
    - Strategy (Behavioral): Swappable with Parakeet, Canary, or
      any other ASR adapter registered in ``NIMRegistry``.

Architecture Layer: Infrastructure
"""

from __future__ import annotations

import asyncio
import io
import logging
import wave
from typing import Optional

from backend.services.nim.protocols import (
    AudioTranscriptionPort,
    NIMConfig,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class RivaWhisperASRClient(AudioTranscriptionPort):
    """
    gRPC adapter for ASR models hosted on NVIDIA Riva / NVCF.

    Uses ``riva.client.ASRService.offline_recognize`` for batch
    (non-streaming) transcription of short audio chunks.

    Constructor params are read from ``NIMConfig``:
        - ``api_key``          → Bearer token for NVCF
        - ``grpc_host``        → e.g. ``grpc.nvcf.nvidia.com``
        - ``grpc_port``        → e.g. ``443``
        - ``grpc_function_id`` → NVCF function UUID for the ASR model
    """

    def __init__(self, config: NIMConfig) -> None:
        self._cfg = config
        self._function_id = config.grpc_function_id
        self._host = f"{config.grpc_host}:{config.grpc_port}"

        logger.info(
            "[Riva:ASR] Initialized client '%s' model='%s' host='%s' function_id='%s'",
            config.name,
            config.model_id,
            self._host,
            self._function_id,
        )

    # ── AudioTranscriptionPort ───────────────────────────────────────────

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio using Riva ASR (gRPC, NVCF).

        The gRPC call is blocking, so we offload it to a thread pool
        via ``run_in_executor`` to keep the asyncio loop responsive.

        Args:
            audio_bytes: WAV (PCM 16-bit, 16 kHz, mono) bytes.
            sample_rate: Source sample rate.
            language:    BCP-47 code, e.g. ``"es"``, ``"en"``.

        Returns:
            TranscriptionResult with the recognized text.
        """
        try:
            text = await asyncio.get_event_loop().run_in_executor(
                None,
                self._recognize_sync,
                audio_bytes,
                sample_rate,
                language,
            )
            return TranscriptionResult(
                text=text,
                language=language,
                confidence=1.0,
            )
        except Exception as exc:
            logger.error(
                "[Riva:ASR] Transcription error: %s — %s",
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            return TranscriptionResult(text="", language=language, confidence=0.0)

    # ── Blocking gRPC call (run in thread pool) ──────────────────────────

    def _recognize_sync(
        self,
        audio_bytes: bytes,
        sample_rate: int,
        language: Optional[str],
    ) -> str:
        """
        Synchronous offline recognition via ``riva.client``.

        Raises on import or gRPC errors; caller handles via fallback.
        """
        import riva.client  # type: ignore

        auth = riva.client.Auth(
            uri=self._host,
            use_ssl=True,
            metadata_args=[
                ["authorization", f"Bearer {self._cfg.api_key}"],
                ["function-id", self._function_id],
            ],
        )

        asr_service = riva.client.ASRService(auth)

        # Map short BCP-47 codes to full locale codes expected by Riva.
        # Canary offline ASR rejects language_code=multi, so default auto to Spanish.
        lang_code = self._normalize_language(language)
        if lang_code == "multi" and "canary" in self._cfg.model_id.lower():
            lang_code = "es-ES"

        config = riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=sample_rate,
            language_code=lang_code,
            max_alternatives=1,
            enable_automatic_punctuation=True,
            audio_channel_count=1,
        )
        if lang_code != "multi":
            config.custom_configuration["source_language"] = lang_code

        # Extract raw PCM from WAV container
        pcm = self._wav_to_pcm(audio_bytes)

        response = asr_service.offline_recognize(pcm, config)

        # Extract best transcript from response
        texts = []
        for result in response.results:
            if result.alternatives:
                texts.append(result.alternatives[0].transcript)

        transcript = " ".join(texts).strip()
        logger.info(
            "[Riva:ASR] Transcribed %d bytes -> %d chars (lang=%s, source_language=%s)",
            len(audio_bytes),
            len(transcript),
            lang_code,
        )
        return transcript

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_language(lang: Optional[str]) -> str:
        """Convert UI language values to Riva locale codes."""
        if not lang or lang.lower() == "auto":
            return "multi"

        normalized = lang.replace("_", "-").lower()
        locale_by_short_code = {
            "en": "en-US",
            "es": "es-ES",
            "fr": "fr-FR",
            "de": "de-DE",
            "pt": "pt-BR",
            "it": "it-IT",
        }
        if "-" in normalized:
            lang_part, region_part = normalized.split("-", 1)
            return f"{lang_part.lower()}-{region_part.upper()}"
        return locale_by_short_code.get(normalized, normalized)


    @staticmethod
    def _wav_to_pcm(wav_bytes: bytes) -> bytes:
        """Extract raw PCM samples from a WAV container."""
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            return wf.readframes(wf.getnframes())
