"""
Transcription Service - Service Layer (SRP / DIP)

Encapsulates all business logic related to transcription CRUD,
search and rendering. Routers delegate to this service instead
of calling repositories directly.

Design Patterns:
    - Service Layer: Centralises domain logic between Routers and
      Repositories so that the Router is a thin HTTP controller.
    - Dependency Injection (DIP): Receives its Repository and
      Renderer via constructor so they can be mocked in tests.

SOLID Principles:
    - SRP: Only responsible for transcription business rules.
    - DIP: Depends on abstractions (Repository, Renderer), not
      concrete implementations.
    - OCP: New business rules can be added without modifying Routers.
"""

from typing import List, Dict, Optional
from backend.repositories.transcription_repository import TranscriptionRepository
from backend.services.knowledge.content_renderer import ContentRenderer


class TranscriptionService:
    """
    Service Layer for Transcription operations.
    
    Encapsulates business logic that was previously scattered
    across the Router endpoints (violating SRP).
    
    Dependency Injection:
        Repository and Renderer are injected via constructor,
        allowing easy mocking in unit tests (DIP).
    """

    def __init__(
        self,
        repository: Optional[TranscriptionRepository] = None,
        renderer: Optional[ContentRenderer] = None,
    ):
        self.repo = repository or TranscriptionRepository()
        self.renderer = renderer or ContentRenderer()

    # ──────── Query operations ────────

    def get_latest(self) -> Dict:
        """
        Get the latest transcription with rendered content.
        
        Returns:
            Dict with id, filename, date, content, is_formatted.
        """
        doc = self.repo.get_latest()
        if not doc:
            return {
                "id": None,
                "filename": None,
                "date": None,
                "content": "# No hay transcripciones disponibles\n\nGraba tu primera clase para comenzar.",
            }

        segments = self.repo.get_segments(doc["_id"])
        content = self.renderer.render_transcription(doc, segments)

        return {
            "id": str(doc["_id"]),
            "filename": doc.get("filename"),
            "date": doc.get("date"),
            "content": content,
            "is_formatted": doc.get("is_formatted", False),
        }

    def get_by_id(self, transcription_id: str) -> Optional[Dict]:
        """
        Get a specific transcription by its ID with rendered content.
        
        Args:
            transcription_id: MongoDB ObjectId as string.
            
        Returns:
            Dict with transcription data or None if not found.
        """
        doc = self.repo.get_by_id(transcription_id)
        if not doc:
            return None

        segments = self.repo.get_segments(doc["_id"])
        content = self.renderer.render_transcription(doc, segments)

        return {
            "id": str(doc["_id"]),
            "filename": doc.get("filename"),
            "date": doc.get("date"),
            "content": content,
            "is_formatted": doc.get("is_formatted", False) or bool(doc.get("formatted_content")),
        }

    def list_recent(self, limit: int = 50) -> List[Dict]:
        """
        List recent transcriptions (metadata only).
        
        Args:
            limit: Maximum number of items.
            
        Returns:
            List of dicts with id, filename, date, is_formatted.
        """
        items_raw = self.repo.list_recent(limit)
        return [
            {
                "id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "date": doc.get("date"),
                "is_formatted": doc.get("is_formatted", False)
                or bool(doc.get("formatted_content")),
            }
            for doc in items_raw
        ]

    # ──────── Search ────────

    def search(self, query: str, limit_docs: int = 20, limit_segs: int = 30) -> List[Dict]:
        """
        Full-text search across transcriptions and segments.
        
        Builds snippet previews and deduplicates results.
        
        Args:
            query: Search string (min 2 chars).
            limit_docs: Max document hits.
            limit_segs: Max segment hits.
            
        Returns:
            List of search-result dicts.
        """
        query = query.strip().strip("'\"")
        if not query or len(query) < 2:
            return []

        res = self.repo.search(query, limit_docs, limit_segs)
        results: List[Dict] = []

        # Format document results
        for doc in res["documents"]:
            content = (
                doc.get("edited_content")
                or doc.get("formatted_content")
                or doc.get("raw_content")
                or ""
            )
            idx = content.lower().find(query.lower())
            display_text = content
            if idx == -1:
                display_text = doc.get("filename", "")
                idx = display_text.lower().find(query.lower())

            snippet = (
                (display_text[max(0, idx - 40): idx + 60].replace("\n", " ") + "...")
                if idx != -1
                else ""
            )

            results.append(
                {
                    "id": str(doc["_id"]),
                    "filename": doc.get("filename"),
                    "date": doc.get("date"),
                    "snippet": snippet,
                    "type": "document",
                    "is_formatted": doc.get("is_formatted", False)
                    or bool(doc.get("formatted_content")),
                }
            )

        # Format segment results (skip duplicates)
        parent_ids = {r["id"] for r in results}
        for seg in res["segments"]:
            t_id = str(seg["transcription_id"])
            if t_id in parent_ids:
                continue
            doc = self.repo.get_by_id(t_id)
            if doc:
                results.append(
                    {
                        "id": t_id,
                        "filename": doc.get("filename"),
                        "date": doc.get("date"),
                        "snippet": seg["content"],
                        "timestamp": seg.get("timestamp"),
                        "type": "segment",
                    }
                )

        return results

    # ──────── Mutations ────────

    def update_content(self, transcription_id: str, content: str) -> bool:
        """Update the editable content of a transcription."""
        return self.repo.update_content(transcription_id, content)

    def delete(self, transcription_id: str) -> bool:
        """Logically delete a transcription."""
        return self.repo.delete(transcription_id)
