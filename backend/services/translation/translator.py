"""
Translation Service (Application Layer) — Mistral Large 3 675B

High-quality multilingual text translation using Mistral Large,
optimised for academic / technical content (transcriptions, notes).

Design Patterns:
    - Service Layer / SRP: only responsible for translating text.
    - Strategy: swappable model via NIMRegistry without changing
      this service (OCP).
    - Facade: exposes a single translate() method hiding all LLM
      prompt engineering and response parsing.

Architecture Layer: Application
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import logfire

from backend.services.nim import NIMRegistry, TranslationResult

logger = logging.getLogger(__name__)


# Human-readable language names used in prompts
_LANG_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "hi": "Hindi",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "sv": "Swedish",
    "auto": "auto-detected",
}


@dataclass
class TranslationRequest:
    """Value Object: inputs for a translation job."""
    text: str
    target_language: str = "es"         # ISO 639-1 code
    source_language: str = "auto"       # "auto" or ISO 639-1 code
    preserve_formatting: bool = True    # Keep markdown, lists, headings
    domain: str = "academic"            # academic | general | technical


class TranslationService:
    """
    Application service for NLP translation via Mistral Large.

    Supports 20+ languages and is optimised for academic transcriptions
    with technical vocabulary.
    """

    def __init__(self, registry: Optional[NIMRegistry] = None) -> None:
        self._registry = registry or NIMRegistry.instance()

    @logfire.instrument("translation.translate")
    async def translate(
        self,
        text: str,
        *,
        target_language: str = "es",
        source_language: str = "auto",
        preserve_formatting: bool = True,
        domain: str = "academic",
    ) -> TranslationResult:
        """
        Translate text to the target language using Mistral Large.

        Args:
            text:                The source text to translate.
            target_language:     ISO 639-1 code of the target language.
            source_language:     ISO 639-1 code of source, or "auto".
            preserve_formatting: If True, maintain markdown structure.
            domain:              Content domain for prompt tuning.

        Returns:
            TranslationResult with translated text and metadata.
        """
        if not text.strip():
            return TranslationResult(
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                model_used="none",
            )

        target_name = _LANG_NAMES.get(target_language, target_language)
        source_name = _LANG_NAMES.get(source_language, source_language)

        system_message = self._build_system_prompt(
            target_name=target_name,
            source_name=source_name,
            preserve_formatting=preserve_formatting,
            domain=domain,
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": text},
        ]

        client = self._registry.get_text("translator")
        model_cfg = self._registry._configs.get("translator")
        model_id = model_cfg.model_id if model_cfg else "mistralai/mistral-large-3"

        translated = await client.generate(
            messages,
            temperature=0.15,
            top_p=1.0,
            max_tokens=min(len(text) * 3, 16000),
        )

        logger.info(
            "[Translation] %s → %s  source=%d chars  result=%d chars",
            source_language,
            target_language,
            len(text),
            len(translated),
        )

        return TranslationResult(
            translated_text=translated.strip(),
            source_language=source_language,
            target_language=target_language,
            model_used=model_id,
        )

    # ── Prompt engineering ───────────────────────────────────────────────

    @staticmethod
    def _build_system_prompt(
        *,
        target_name: str,
        source_name: str,
        preserve_formatting: bool,
        domain: str,
    ) -> str:
        """
        Build a domain-specific system prompt for high-quality translation.
        """
        formatting_instruction = (
            "Preserve all markdown formatting exactly: headings (#), "
            "bold (**), italic (*), bullet lists (-/•), numbered lists, "
            "code blocks, and tables."
            if preserve_formatting
            else "Output plain text only."
        )

        domain_instruction = {
            "academic": (
                "This is an academic lecture transcription. "
                "Preserve technical terminology accurately. "
                "Use formal register appropriate for university contexts."
            ),
            "technical": (
                "This is technical documentation. "
                "Keep all technical terms, acronyms, and proper nouns unchanged. "
                "Do not translate variable names, commands, or code snippets."
            ),
            "general": "Apply natural, fluent translation suitable for general audiences.",
        }.get(domain, "Apply accurate and fluent translation.")

        source_clause = (
            "The source language is auto-detected."
            if source_name == "auto-detected"
            else f"The source language is {source_name}."
        )

        return (
            f"You are an expert translator. {source_clause}\n"
            f"Translate the following text into {target_name}.\n"
            f"{domain_instruction}\n"
            f"{formatting_instruction}\n"
            "Output ONLY the translated text. "
            "Do NOT add explanations, notes, or commentary."
        )
