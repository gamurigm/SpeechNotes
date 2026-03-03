"""
Audio Processing Router — Interface Layer

HTTP endpoints for:
  POST /api/audio/transcribe   — ASR via Parakeet (upload WAV/MP3/WebM)
  POST /api/audio/denoise      — BNR via gRPC (upload WAV, returns cleaned WAV)
  POST /api/audio/pipeline    — Full pipeline: BNR → ASR → Translation

Design: thin router — all logic delegated to service layer (SRP).
Auth: require_auth dependency (set globally in main.py per router).
"""

from __future__ import annotations

import io
import logging
from typing import Optional

import logfire
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from backend.services.audio import ASRRequest, ASRService, NoiseRemovalRequest, NoiseRemovalService
from backend.services.audio.pipeline import PipelineContext, PipelineFactory

logger = logging.getLogger(__name__)
router = APIRouter()


# ── POST /api/audio/transcribe ──────────────────────────────────────────

@router.post(
    "/transcribe",
    summary="Transcribe audio using Parakeet TDT 0.6B v2",
    tags=["audio"],
)
@logfire.instrument("router.audio.transcribe")
async def transcribe_audio(
    file: UploadFile = File(..., description="WAV, MP3, WebM, or OGG audio file"),
    language: Optional[str] = Form(None, description="BCP-47 language hint e.g. 'en', 'es'"),
    translate_to: Optional[str] = Form(None, description="Translate result to this language (ISO 639-1)"),
):
    """
    Transcribe an audio file using NVIDIA Parakeet TDT 0.6B v2.

    - Accepts WAV, MP3, WebM, OGG (converted internally to 16kHz mono PCM).
    - Optionally translate the transcript via Mistral Large.
    - Returns the raw transcript text and detected language.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(400, "Uploaded file is empty")

    svc = ASRService()
    result = await svc.transcribe(
        ASRRequest(
            audio_bytes=audio_bytes,
            language=language,
            translate_to=translate_to,
        )
    )

    return {
        "text": result.text,
        "language": result.language,
        "confidence": result.confidence,
        "duration_seconds": result.duration_seconds,
    }


# ── POST /api/audio/denoise ─────────────────────────────────────────────

@router.post(
    "/denoise",
    summary="Remove background noise using NVIDIA BNR NIM (gRPC)",
    tags=["audio"],
    response_class=Response,
)
@logfire.instrument("router.audio.denoise")
async def denoise_audio(
    file: UploadFile = File(..., description="WAV audio file (16-bit PCM, 16kHz, mono)"),
    sample_rate: int = Form(16000, description="Input sample rate in Hz"),
):
    """
    Clean background noise from a WAV file using NVIDIA BNR NIM.

    Returns the denoised audio as `audio/wav`.
    If BNR is not configured, returns the original audio unchanged
    (passthrough mode — no error, just a header `X-BNR-Mode: passthrough`).
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(400, "Uploaded file is empty")

    svc = NoiseRemovalService()
    result = await svc.denoise(
        NoiseRemovalRequest(audio_bytes=audio_bytes, sample_rate=sample_rate)
    )

    return Response(
        content=result.audio_bytes,
        media_type="audio/wav",
        headers={
            "X-BNR-Mode": result.enhancement_applied,
            "X-Sample-Rate": str(result.sample_rate),
        },
    )


# ── POST /api/audio/pipeline ────────────────────────────────────────────

@router.post(
    "/pipeline",
    summary="Full audio pipeline: BNR → ASR → Translation",
    tags=["audio"],
)
@logfire.instrument("router.audio.pipeline")
async def run_pipeline(
    file: UploadFile = File(..., description="Audio file"),
    pipeline: str = Form("full", description="Pipeline variant: full | asr_only | denoise | passthrough"),
    language: Optional[str] = Form(None, description="Language hint (BCP-47)"),
    translate_to: Optional[str] = Form(None, description="Translate transcript to this language"),
    sample_rate: int = Form(16000, description="Input sample rate"),
):
    """
    Run the full audio processing pipeline:

    **full**: BNR (noise removal) → Parakeet (ASR) → Mistral (translation)
    **asr_only**: Parakeet → Mistral (skip BNR)
    **denoise**: BNR only (returns cleaned audio metadata, not the WAV)
    **passthrough**: Identity pipeline for testing

    Returns a JSON summary with transcript, translations, and errors.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(400, "Uploaded file is empty")

    try:
        pipe = PipelineFactory.create(pipeline)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    ctx = PipelineContext(
        audio_bytes=audio_bytes,
        sample_rate=sample_rate,
        language_hint=language,
        translate_to=translate_to,
    )

    result_ctx = await pipe.run(ctx)

    return {
        "pipeline": pipeline,
        "transcript": result_ctx.transcript,
        "translated_text": result_ctx.translated_text,
        "detected_language": result_ctx.detected_language,
        "errors": result_ctx.errors,
        "bnr_applied": result_ctx.cleaned_audio is not None,
    }
