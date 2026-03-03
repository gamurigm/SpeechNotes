"""
NIM Service Protocols — Infrastructure Layer (Abstract Interfaces)

Defines the contracts that all NIM clients must implement.

Design Patterns:
    - Interface Segregation Principle (ISP): Separate protocols for
      text generation, audio transcription, and audio transformation
      so clients only implement what they support.
    - Dependency Inversion Principle (DIP): Application and domain
      layers depend on these abstractions, not on concrete NIM clients.
    - Template Method: BaseNIMClient provides the processing pipeline
      skeleton; subclasses override specific steps.

Architecture Layer: Infrastructure / Port (Hexagonal Architecture)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import AsyncIterator, Optional


# ──────────────────────────────────────────────────────────
# Value Objects (Domain-safe, immutable)
# ──────────────────────────────────────────────────────────

class NIMClientType(Enum):
    """Discriminates how a NIM endpoint is reached."""
    HTTP_OPENAI  = auto()   # OpenAI-compatible REST (most models)
    GRPC         = auto()   # Binary gRPC streaming (BNR, Riva)


@dataclass(frozen=True)
class NIMConfig:
    """
    Immutable configuration for a NIM endpoint.

    Frozen dataclass prevents accidental mutation after construction
    (Value Object pattern), and is hashable so it can be used as a
    dict key in the registry.
    """
    name: str                          # Human-readable identifier
    api_key: str                       # nvapi-* credential
    base_url: str = "https://integrate.api.nvidia.com/v1"
    model_id: str = ""                 # e.g. "qwen/qwen3.5-397b-a17b"
    client_type: NIMClientType = NIMClientType.HTTP_OPENAI
    grpc_host: str = "grpc.nvcf.nvidia.com"
    grpc_port: int = 443
    grpc_function_id: str = ""         # NVCF function UUID (gRPC only)
    extra: dict = field(default_factory=dict, compare=False, hash=False)


@dataclass
class TranscriptionResult:
    """
    Result from any ASR (Automatic Speech Recognition) service.
    Decoupled from any specific model's response schema.
    """
    text: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    confidence: float = 1.0


@dataclass
class AudioCleanResult:
    """Result from a noise-removal / audio-enhancement service."""
    audio_bytes: bytes
    sample_rate: int = 16000
    channels: int = 1
    enhancement_applied: str = "bnr"


@dataclass
class TranslationResult:
    """Result from a translation service."""
    translated_text: str
    source_language: str
    target_language: str
    model_used: str


@dataclass
class DetectionResult:
    """Result from a language-detection service."""
    language_code: str        # ISO 639-1 (e.g. "en", "es")
    language_name: str        # Human-readable
    confidence: float


# ──────────────────────────────────────────────────────────
# Port Interfaces (ISP: one per capability)
# ──────────────────────────────────────────────────────────

class TextGenerationPort(ABC):
    """
    Port for text generation (chat completions).

    Models: qwen3.5-397b-a17b, mistral-large-3, gemma-3n, etc.
    """

    @abstractmethod
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
        """Single-shot text generation (stream=False)."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 8192,
        **extra,
    ) -> AsyncIterator[str]:
        """Token-by-token streaming generation."""
        ...


class AudioTranscriptionPort(ABC):
    """
    Port for speech-to-text (ASR).

    Models: parakeet-tdt-0.6b-v2, Whisper variants.
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        ...


class AudioEnhancementPort(ABC):
    """
    Port for audio pre-processing (noise removal, enhancement).

    Models: NVIDIA BNR NIM (gRPC).
    """

    @abstractmethod
    async def denoise(
        self,
        audio_bytes: bytes,
        *,
        sample_rate: int = 16000,
    ) -> AudioCleanResult:
        ...


class LanguageDetectionPort(ABC):
    """Port for language identification."""

    @abstractmethod
    async def detect(self, text: str) -> DetectionResult:
        ...


class TranslationPort(ABC):
    """Port for text translation."""

    @abstractmethod
    async def translate(
        self,
        text: str,
        *,
        target_language: str = "es",
        source_language: str = "auto",
    ) -> TranslationResult:
        ...
