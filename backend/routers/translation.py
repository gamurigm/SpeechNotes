"""
Translation Router — Interface Layer

HTTP endpoints for:
  POST /api/translate           — Translate text (Mistral Large)
  POST /api/translate/detect    — Detect language (Gemma 3n)
  POST /api/translate/batch     — Translate multiple transcriptions

Design: thin router — all logic delegated to service layer (SRP).
"""

from __future__ import annotations

import logging
from typing import List, Optional

import logfire
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.translation import LanguageDetectionService, TranslationService

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response Schemas (Pydantic) ────────────────────────────────

class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate", min_length=1)
    target_language: str = Field("es", description="Target language ISO 639-1 code")
    source_language: str = Field("auto", description="Source language ISO 639-1 code or 'auto'")
    preserve_formatting: bool = Field(True, description="Keep markdown formatting")
    domain: str = Field(
        "academic",
        description="Content domain: academic | technical | general",
    )


class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    model_used: str


class DetectRequest(BaseModel):
    text: str = Field(..., description="Text sample (50–500 chars for best accuracy)")


class DetectResponse(BaseModel):
    language_code: str
    language_name: str
    confidence: float


class BatchTranslateItem(BaseModel):
    id: str
    text: str


class BatchTranslateRequest(BaseModel):
    items: List[BatchTranslateItem]
    target_language: str = "es"
    source_language: str = "auto"
    domain: str = "academic"


class BatchTranslateResponse(BaseModel):
    results: List[dict]


# ── POST /api/translate ──────────────────────────────────────────────────

@router.post(
    "/",
    response_model=TranslateResponse,
    summary="Translate text using Mistral Large 3 675B",
)
@logfire.instrument("router.translate")
async def translate_text(req: TranslateRequest) -> TranslateResponse:
    """
    Translate text to the specified target language.

    Uses **Mistral Large 3 675B** (mistralai/mistral-large-3-675b-instruct-2512)
    tuned for academic / technical content.

    Supported domains: `academic` (default), `technical`, `general`.
    Supported languages: en, es, fr, de, pt, it, zh, ja, ko, ar, ru,
    hi, nl, pl, tr, sv, da, fi, no, and more.
    """
    svc = TranslationService()
    result = await svc.translate(
        req.text,
        target_language=req.target_language,
        source_language=req.source_language,
        preserve_formatting=req.preserve_formatting,
        domain=req.domain,
    )
    return TranslateResponse(
        translated_text=result.translated_text,
        source_language=result.source_language,
        target_language=result.target_language,
        model_used=result.model_used,
    )


# ── POST /api/translate/detect ───────────────────────────────────────────

@router.post(
    "/detect",
    response_model=DetectResponse,
    summary="Detect language using Gemma 3n E4B",
)
@logfire.instrument("router.translate.detect")
async def detect_language(req: DetectRequest) -> DetectResponse:
    """
    Identify the language of a text snippet.

    Uses **Google Gemma 3n E4B** for fast, lightweight language
    classification.  Returns ISO 639-1 code, language name, and
    confidence score.
    """
    svc = LanguageDetectionService()
    result = await svc.detect(req.text)
    return DetectResponse(
        language_code=result.language_code,
        language_name=result.language_name,
        confidence=result.confidence,
    )


# ── POST /api/translate/batch ────────────────────────────────────────────

@router.post(
    "/batch",
    response_model=BatchTranslateResponse,
    summary="Batch translate multiple text items",
)
@logfire.instrument("router.translate.batch")
async def batch_translate(req: BatchTranslateRequest) -> BatchTranslateResponse:
    """
    Translate multiple text items in parallel.

    Each item requires an `id` (returned in results for correlation)
    and a `text` field.  Returns one result per input item.

    Use this to translate multiple transcription segments or notes at once.
    """
    import asyncio

    svc = TranslationService()

    async def translate_one(item: BatchTranslateItem) -> dict:
        try:
            result = await svc.translate(
                item.text,
                target_language=req.target_language,
                source_language=req.source_language,
                domain=req.domain,
            )
            return {
                "id": item.id,
                "translated_text": result.translated_text,
                "target_language": result.target_language,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("[BatchTranslate] item %s failed: %s", item.id, exc)
            return {"id": item.id, "translated_text": None, "error": str(exc)}

    results = await asyncio.gather(*(translate_one(i) for i in req.items))
    return BatchTranslateResponse(results=list(results))
