"""
Transcriptions Router - Controller Layer (SRP)

Handles HTTP requests for transcription resources and delegates
business logic to the TranscriptionService.

Refactoring:
    - Removed business logic (formatting, search aggregation) to Service.
    - Implemented Dependency Injection for TranscriptionService.
    - Enforced SRP: This router is now only responsible for HTTP I/O.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Annotated, List, Optional

from backend.services.audio.transcription_service import TranscriptionService
from backend.repositories.transcription_repository import TranscriptionRepository
from backend.services.knowledge.content_renderer import ContentRenderer

router = APIRouter()
NOT_FOUND_MESSAGE = "Not found"


# ──────────────────────────────────────────────
#  Dependency Injection (DIP)
# ──────────────────────────────────────────────

def get_service():
    """
    Dependency provider for TranscriptionService.
    Can be overridden in tests to inject mocks.
    """
    return TranscriptionService(
        repository=TranscriptionRepository(),
        renderer=ContentRenderer()
    )


class TranscriptionUpdate(BaseModel):
    content: str


# Endpoint definitions follow.

@router.get("/latest", responses={500: {"description": "Error al obtener última transcripción"}})
async def get_latest_transcription(service: Annotated[TranscriptionService, Depends(get_service)]):
    """Get the latest processed transcription (delegates to Service)."""
    try:
        return service.get_latest()
    except Exception as e:
        print(f"[ERROR] /api/transcriptions/latest: {e}")
        # traceback.print_exc() # Optional: keep logs clean or verbose as needed
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("", responses={500: {"description": "Error al listar transcripciones"}})
async def list_transcriptions(
    service: Annotated[TranscriptionService, Depends(get_service)],
    limit: int = 50,
):
    """List recent processed transcriptions (metadata only)."""
    try:
        items = service.list_recent(limit)
        return {"items": items}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/search", responses={500: {"description": "Error en búsqueda"}})
async def search_transcriptions(
    service: Annotated[TranscriptionService, Depends(get_service)],
    q: str,
):
    """Global search using Service Layer logic."""
    try:
        results = service.search(q)
        return {"items": results}
    except Exception as e:
        raise HTTPException(500, f"Search error: {str(e)}")


@router.get("/{transcription_id}", responses={404: {"description": "Transcripción no encontrada"}, 500: {"description": "Error al obtener transcripción"}})
async def get_transcription_by_id(
    service: Annotated[TranscriptionService, Depends(get_service)],
    transcription_id: str,
):
    """Get a specific processed transcription by id."""
    try:
        doc = service.get_by_id(transcription_id)
        if not doc:
            raise HTTPException(404, NOT_FOUND_MESSAGE)
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@router.put("/{transcription_id}", responses={404: {"description": "Transcripción no encontrada"}})
async def update_transcription(
    service: Annotated[TranscriptionService, Depends(get_service)],
    transcription_id: str,
    update: TranscriptionUpdate,
):
    """Update transcription content."""
    if service.update_content(transcription_id, update.content):
        return {"status": "updated"}
    raise HTTPException(404, NOT_FOUND_MESSAGE)


@router.delete("/{transcription_id}", responses={404: {"description": "Transcripción no encontrada"}})
async def delete_transcription(
    service: Annotated[TranscriptionService, Depends(get_service)],
    transcription_id: str,
):
    """Logically delete a transcription."""
    if service.delete(transcription_id):
        return {"status": "deleted"}
    raise HTTPException(404, NOT_FOUND_MESSAGE)
