"""
Language Detector Service (Application Layer) — Gemma 3n E4B

Fast, lightweight language identification using Google Gemma 3n, a
multimodal model optimised for edge-deployment speed.

Design Patterns:
    - Service Layer / SRP: only responsible for "what language is this?".
    - Strategy: NIMRegistry can swap Gemma for any TextGenerationPort
      without modifying this service.
    - Null Object: returns DetectionResult("unknown", confidence=0)
      on failure instead of raising.

Architecture Layer: Application
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

import logfire

from backend.services.nim import DetectionResult, NIMRegistry

logger = logging.getLogger(__name__)

# Supported languages with their ISO 639-1 codes
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "hi": "Hindi",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "unknown": "Unknown",
}


class LanguageDetectionService:
    """Detect the language of a text snippet using Gemma 3n."""

    def __init__(self, registry: Optional[NIMRegistry] = None) -> None:
        self._registry = registry or NIMRegistry.instance()

    @logfire.instrument("nlp.detect_language")
    async def detect(self, text: str) -> DetectionResult:
        """
        Identify the language of `text`.

        Uses Gemma 3n with a JSON-structured prompt for deterministic
        output parsing.

        Args:
            text: Text sample (50–500 chars works best).

        Returns:
            DetectionResult with ISO code, name, and confidence.
        """
        if not text.strip():
            return DetectionResult("unknown", "Unknown", 0.0)

        # Truncate to avoid wasting tokens on very long texts
        sample = text.strip()[:400]

        prompt = (
            "Identify the language of the following text. "
            "Reply with ONLY a JSON object in this exact format:\n"
            '{"language_code": "<ISO 639-1>", "language_name": "<English name>", "confidence": <0.0-1.0>}\n\n'
            f"Text: {sample}"
        )

        try:
            client = self._registry.get_text("detector")
            raw = await client.generate(
                [{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=64,
            )
            return self._parse(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[LanguageDetect] Error: %s", exc)
            return DetectionResult("unknown", "Unknown", 0.0)

    @staticmethod
    def _parse(raw: str) -> DetectionResult:
        """Extract the JSON detection result from the model response."""
        try:
            # Strip markdown code blocks
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            data = json.loads(clean)
            code = data.get("language_code", "unknown").lower()[:5]
            name = data.get("language_name") or LANGUAGE_NAMES.get(code, "Unknown")
            confidence = float(data.get("confidence", 1.0))
            return DetectionResult(code, name, confidence)
        except Exception:
            # Fall back to heuristic: look for a known code in the text
            lower = raw.lower()
            for code in LANGUAGE_NAMES:
                if code in lower:
                    return DetectionResult(code, LANGUAGE_NAMES[code], 0.7)
            return DetectionResult("unknown", "Unknown", 0.0)
