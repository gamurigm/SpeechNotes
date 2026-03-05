"""
Chat API Router - Uses Pydantic AI Agent with Document Context
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
import json
import re

# Database
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.database import MongoManager

# Pydantic AI Agent
from services.agents.pydantic_agent import (
    DocumentContext,
    chat_stream_direct,
    chat_stream_with_document,
)

router = APIRouter()
logger = logging.getLogger(__name__)
db = MongoManager()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    doc_id: Optional[str] = None       # SQLite document id (uuid hex)
    active_file: Optional[str] = None  # Deprecated but kept for backwards compat
    doc_content: Optional[str] = None  # Pre-loaded content from frontend (avoids DB lookup)
    thinking: bool = True              # Whether to use the thinking/reasoning capability


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []


def load_document_context(doc_id: str) -> Optional[DocumentContext]:
    """
    Load document content from SQLite and create a DocumentContext.
    doc_id is a plain string (uuid hex) or filename-based identifier.
    """
    try:
        if not doc_id or not doc_id.strip():
            return None

        doc = db.transcriptions.find_one({"_id": doc_id})
        if not doc:
            # Fallback: maybe doc_id is a filename
            doc = db.transcriptions.find_one({"filename": doc_id})
        
        if not doc:
            logger.warning(f"Document not found: {doc_id}")
            return None
        
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
            # Try segments
            segments = list(db.segments.find(
                {"transcription_id": doc["_id"]}
            ).sort("sequence", 1))
            
            if segments:
                content = "\n\n".join(seg.get("text", "") for seg in segments)
                content_type = "segments"
            else:
                content = "No content available."
                content_type = "empty"
        
        # Extract title
        title = doc.get("title")
        if not title and content:
            heading_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1).strip()
        
        return DocumentContext(
            doc_id=str(doc["_id"]),
            filename=doc.get("filename"),
            title=title,
            content=content,
            content_type=content_type
        )
        
    except Exception as e:
        logger.exception(f"Error loading document context for {doc_id}")
        return None


def load_document_by_filename(filename: str) -> Optional[DocumentContext]:
    """
    Fallback: Load document by filename (backwards compat with active_file).
    """
    try:
        # Try exact match first
        doc = db.transcriptions.find_one({"filename": filename})
        
        if not doc:
            # Try partial match
            doc = db.transcriptions.find_one({
                "filename": {"$regex": filename.replace('.md', '').replace('.wav', ''), "$options": "i"}
            })
        
        if not doc:
            logger.warning(f"Document not found by filename: {filename}")
            return None
            
        return load_document_context(str(doc["_id"]))
        
    except Exception as e:
        logger.exception(f"Error loading document by filename: {filename}")
        return None


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint with document context awareness.
    
    Priority for document context:
    1. doc_id (SQLite id) - preferred
    2. active_file (filename) - backwards compat
    3. Most recent document - fallback
    """
    try:
        # Get the last user message as query
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query = user_messages[-1].content
        
        # Load document context with priority:
        # 0. doc_content (pre-loaded content from frontend) — fastest, no DB needed
        # 1. doc_id (SQLite uuid)
        # 2. active_file (filename) — backwards compat
        # 3. most recent document — fallback
        document: Optional[DocumentContext] = None

        if request.doc_content and len(request.doc_content.strip()) > 20:
            logger.info("Using pre-loaded doc_content from frontend (bypassing DB lookup)")
            # Derive a display name from doc_id or active_file
            doc_label = request.doc_id or request.active_file or "documento-activo"
            heading_match = re.match(r'^#\s+(.+)$', request.doc_content, re.MULTILINE)
            title = heading_match.group(1).strip() if heading_match else None
            document = DocumentContext(
                doc_id=doc_label,
                filename=request.active_file,
                title=title,
                content=request.doc_content,
                content_type="frontend"
            )
        elif request.doc_id:
            logger.info(f"Loading document by doc_id: {request.doc_id}")
            document = load_document_context(request.doc_id)
        elif request.active_file:
            logger.info(f"Loading document by filename (deprecated): {request.active_file}")
            document = load_document_by_filename(request.active_file)
        
        if not document:
            # Fallback to most recent document
            logger.info("No document specified, loading most recent")
            # First try with ingested_at
            latest = db.transcriptions.find_one(
                {"is_deleted": {"$ne": True}},
                sort=[("ingested_at", -1)]
            )
            # If not found, try any document (some docs might miss ingested_at)
            if not latest:
                latest = db.transcriptions.find_one(
                    {"is_deleted": {"$ne": True}},
                    sort=[("_id", -1)]
                )
            
            if latest:
                document = load_document_context(str(latest["_id"]))
        
        if not document:
            # Create a minimal context
            document = DocumentContext(
                doc_id="none",
                filename=None,
                title="Sin documento",
                content="No hay documentos disponibles. Por favor graba una transcripción primero.",
                content_type="empty"
            )
        
        logger.info(f"Chat request: query='{query[:50]}...', doc={document.filename}, type={document.content_type}")
        
        async def generate():
            try:
                # Initial status message
                status = {
                    "content": f"[Analizando: {document.title or document.filename or 'documento'}...]\n\n",
                    "done": False,
                    "doc_id": document.doc_id,
                    "doc_name": document.filename
                }
                yield f"data: {json.dumps(status)}\n\n"
                
                # Stream from agent (using direct API for reliability)
                async for chunk in chat_stream_direct(query, document, thinking=request.thinking):
                    data = json.dumps({"content": chunk, "done": False})
                    yield f"data: {data}\n\n"
                
                # Done signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.exception("Error in chat stream generator")
                error_data = json.dumps({"error": str(e), "done": True})
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in chat endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint (for compatibility)."""
    try:
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query = user_messages[-1].content
        
        # Load document
        document = None
        if request.doc_id:
            document = load_document_context(request.doc_id)
        elif request.active_file:
            document = load_document_by_filename(request.active_file)
        
        if not document:
            return ChatResponse(
                answer="No hay documento disponible para analizar.",
                sources=[]
            )
        
        # Collect all chunks
        response_text = ""
        async for chunk in chat_stream_direct(query, document):
            response_text += chunk
        
        return ChatResponse(
            answer=response_text,
            sources=[{"doc_id": document.doc_id, "filename": document.filename}]
        )
        
    except Exception as e:
        logger.exception("Error in non-streaming chat")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
async def trigger_indexing():
    """Legacy endpoint for compatibility."""
    return {"message": "Indexing not needed with document-based approach"}
