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
from typing import List, Optional

from backend.services.transcription_service import TranscriptionService
from backend.repositories.transcription_repository import TranscriptionRepository
from backend.services.content_renderer import ContentRenderer

router = APIRouter()


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


# ──────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────

@router.get("/latest")
async def get_latest_transcription(service: TranscriptionService = Depends(get_service)):
    """Get the latest processed transcription (delegates to Service)."""
    try:
        return service.get_latest()
    except Exception as e:
        print(f"[ERROR] /api/transcriptions/latest: {e}")
        # traceback.print_exc() # Optional: keep logs clean or verbose as needed
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/")
async def list_transcriptions(
    limit: int = 50,
    service: TranscriptionService = Depends(get_service)
):
    """List recent processed transcriptions (metadata only)."""
    try:
        items = service.list_recent(limit)
        return {"items": items}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/search")
async def search_transcriptions(
    q: str,
    service: TranscriptionService = Depends(get_service)
):
    """Global search using Service Layer logic."""
    try:
        results = service.search(q)
        return {"items": results}
    except Exception as e:
        raise HTTPException(500, f"Search error: {str(e)}")


@router.get("/{transcription_id}")
async def get_transcription_by_id(
    transcription_id: str,
    service: TranscriptionService = Depends(get_service)
):
    """Get a specific processed transcription by id."""
    try:
        doc = service.get_by_id(transcription_id)
        if not doc:
            raise HTTPException(404, "Not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@router.put("/{transcription_id}")
async def update_transcription(
    transcription_id: str,
    update: TranscriptionUpdate,
    service: TranscriptionService = Depends(get_service)
):
    """Update transcription content."""
    if service.update_content(transcription_id, update.content):
        return {"status": "updated"}
    raise HTTPException(404, "Not found")


@router.delete("/{transcription_id}")
async def delete_transcription(
    transcription_id: str,
    service: TranscriptionService = Depends(get_service)
):
    """Logically delete a transcription."""
    if service.delete(transcription_id):
        return {"status": "deleted"}
    raise HTTPException(404, "Not found")
