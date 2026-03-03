"""backend/services/nim — NIM client infrastructure package."""
from backend.services.nim.registry import NIMRegistry
from backend.services.nim.protocols import (
    NIMConfig,
    NIMClientType,
    TranscriptionResult,
    AudioCleanResult,
    TranslationResult,
    DetectionResult,
)

__all__ = [
    "NIMRegistry",
    "NIMConfig",
    "NIMClientType",
    "TranscriptionResult",
    "AudioCleanResult",
    "TranslationResult",
    "DetectionResult",
]
