"""
OpenAI-Compatible NIM Client — Infrastructure Layer

Concrete adapter for all NVIDIA NIM endpoints that expose the
OpenAI chat completions and audio transcriptions REST APIs.

Design Patterns:
    - Adapter (Structural): Wraps the openai Python SDK behind
      the NIM port interfaces so the rest of the app never
      imports openai directly.
    - Template Method (Behavioral): _build_headers() and
      _build_payload() are overridable hooks used by subclasses
      such as ThinkingNIMClient.
    - Singleton (Creational): enforced via NIMRegistry; this class
      itself is not a singleton so it can be unit-tested in
      isolation without global state.

Architecture Layer: Infrastructure
"""

from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

import httpx
from openai import AsyncOpenAI

from backend.services.nim.protocols import (
    AudioTranscriptionPort,
    NIMConfig,
    TextGenerationPort,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class OpenAINIMClient(TextGenerationPort, AudioTranscriptionPort):
    """
    Adapter around AsyncOpenAI that talks to NVIDIA NIM endpoints.

    Implements both TextGenerationPort and AudioTranscriptionPort
    because parakeet also uses the OpenAI audio/transcriptions route.
    """

    def __init__(self, config: NIMConfig) -> None:
        self._cfg = config
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            http_client=httpx.AsyncClient(timeout=120.0),
        )
        logger.info(
            "[NIM:HTTP] Initialized client '%s' → model='%s'",
            config.name,
            config.model_id,
        )

    # ── Template Method hooks (overridable by subclasses) ────────────────

    def _build_extra_params(self, **override) -> dict:
        """Merge config-level extras with per-call overrides."""
        return {**self._cfg.extra, **override}

    # ── TextGenerationPort ───────────────────────────────────────────────

    async def generate(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 8192,
        stream: bool = False,
        **extra,
    ) -> str:
        """Non-streaming chat completion."""
        params = self._build_extra_params(**extra)
        completion = await self._client.chat.completions.create(
            model=self._cfg.model_id,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=False,
            **params,
        )
        return completion.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 8192,
        **extra,
    ) -> AsyncIterator[str]:
        """Token-by-token streaming chat completion."""
        params = self._build_extra_params(**extra)
        async with await self._client.chat.completions.create(
            model=self._cfg.model_id,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=True,
            **params,
        ) as response:
            async for chunk in response:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta

    # ── AudioTranscriptionPort ───────────────────────────────────────────

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio using the OpenAI-compatible audio/transcriptions
        endpoint.  Parakeet-TDT-0.6B-v2 is exposed via this route.

        Args:
            audio_bytes: Raw WAV (PCM 16-bit, 16kHz, mono) bytes.
            sample_rate: Source sample rate (informational).
            language:    BCP-47 language hint e.g. "en". None = auto.
        """
        import io

        # The SDK expects a file-like object with a .name attribute
        # so it can infer the MIME type from the extension.
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"

        kwargs: dict = {"model": self._cfg.model_id, "file": audio_file}
        if language:
            kwargs["language"] = language

        response = await self._client.audio.transcriptions.create(**kwargs)
        return TranscriptionResult(
            text=response.text,
            language=language,
            confidence=1.0,
        )


class ThinkingNIMClient(OpenAINIMClient):
    """
    Specialisation of OpenAINIMClient for models that support
    extended thinking (Qwen 3.5, DeepSeek-R1).

    Adds chat_template_kwargs to enable the thinking chain before
    the final answer is emitted.

    Design Pattern: Template Method — overrides _build_extra_params
    to inject the thinking flag without duplicating generate/stream.
    """

    def _build_extra_params(self, **override) -> dict:
        base = super()._build_extra_params(**override)
        base.setdefault("chat_template_kwargs", {"enable_thinking": True})
        return base
