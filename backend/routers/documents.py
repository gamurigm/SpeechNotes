"""
Documents API Router - Exposes document content for AI consumption
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.database import MongoManager
import logging

router = APIRouter()
db = MongoManager()
logger = logging.getLogger(__name__)


class DocumentContent(BaseModel):
    """Document content response model"""
    id: str
    filename: Optional[str] = None
    title: Optional[str] = None
    content: str
    content_type: str  # 'formatted', 'raw', 'edited'


class DocumentMetadata(BaseModel):
    """Document metadata for listing"""
    id: str
    filename: Optional[str] = None
    date: Optional[str] = None
    has_content: bool


@router.get("/{doc_id}/content", response_model=DocumentContent)
async def get_document_content(doc_id: str):
    """
    Get the plain text content of a document by its ID.

    Returns the best available content in order of preference:
    1. edited_content (if user has edited)
    2. formatted_content (AI-formatted version)
    3. raw_content (original transcription)
    """
    try:
        if not doc_id or not doc_id.strip():
            raise HTTPException(status_code=400, detail="Invalid document ID")

        doc = db.transcriptions.find_one({"_id": doc_id})
        if not doc:
            # Fallback: maybe doc_id is actually a filename
            doc = db.transcriptions.find_one({"filename": doc_id})

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Determine best content source
        content = None
        content_type = None
        
        if doc.get("edited_content"):
            content = doc["edited_content"]
            content_type = "edited"
        elif doc.get("formatted_content"):
            content = doc["formatted_content"]
            content_type = "formatted"
        elif doc.get("raw_content"):
            content = doc["raw_content"]
            content_type = "raw"
        else:
            # Try to build content from segments
            segments = list(db.segments.find(
                {"transcription_id": doc["_id"]}
            ).sort("sequence", 1))
            
            if segments:
                content = "\n\n".join(seg.get("text", "") for seg in segments)
                content_type = "segments"
            else:
                content = "No content available for this document."
                content_type = "empty"
        
        # Extract title from content if not in metadata
        title = doc.get("title")
        if not title and content:
            # Try to extract from first markdown heading
            import re
            heading_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1).strip()
        
        logger.info(f"Document {doc_id} content retrieved, type: {content_type}, length: {len(content)}")
        
        return DocumentContent(
            id=str(doc["_id"]),
            filename=doc.get("filename"),
            title=title,
            content=content,
            content_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching document {doc_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[DocumentMetadata])
async def list_documents(limit: int = 50):
    """
    List available documents with metadata.
    Used for document selection in the UI.
    """
    try:
        cursor = db.transcriptions.find(
            {"processed": True}
        ).sort("ingested_at", -1).limit(limit)
        
        items = []
        for doc in cursor:
            has_content = bool(
                doc.get("edited_content") or 
                doc.get("formatted_content") or 
                doc.get("raw_content")
            )
            
            items.append(DocumentMetadata(
                id=str(doc.get("_id")),
                filename=doc.get("filename"),
                date=str(doc.get("date")) if doc.get("date") else None,
                has_content=has_content
            ))
        
        return items
        
    except Exception as e:
        logger.exception("Error listing documents")
        raise HTTPException(status_code=500, detail=str(e))
