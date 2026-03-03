"""backend/services/translation — translation & language services package."""
from backend.services.translation.detector import LanguageDetectionService
from backend.services.translation.translator import TranslationService, TranslationRequest

__all__ = [
    "LanguageDetectionService",
    "TranslationService",
    "TranslationRequest",
]
