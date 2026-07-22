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
            logger.warning("Requested document was not found")
            return None
        
        content, content_type = _document_content(doc)
        
        # Extract title
        title = doc.get("title")
        if not title and content:
            heading_match = re.match(r'^#[ \t]+([^\r\n]+)$', content, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1).strip()
        
        return DocumentContext(
            doc_id=str(doc["_id"]),
            filename=doc.get("filename"),
            title=title,
            content=content,
            content_type=content_type
        )
        
    except Exception:
        logger.exception("Error loading requested document context")
        return None


def _document_content(doc: dict) -> tuple[str, str]:
    """Select the best available content representation for a document."""
    for field, content_type in (("edited_content", "edited"), ("formatted_content", "formatted"), ("raw_content", "raw")):
        content = doc.get(field)
        if content:
            return content, content_type

    segments = list(db.segments.find({"transcription_id": doc["_id"]}).sort("sequence", 1))
    if segments:
        return "\n\n".join(seg.get("text", "") for seg in segments), "segments"
    return "No content available.", "empty"


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
                "filename": {"$regex": re.escape(filename.replace('.md', '').replace('.wav', '')), "$options": "i"}
            })
        
        if not doc:
            logger.warning("Requested document filename was not found")
            return None
            
        return load_document_context(str(doc["_id"]))
        
    except Exception:
        logger.exception("Error loading requested document by filename")
        return None


def _frontend_document(request: ChatRequest) -> Optional[DocumentContext]:
    if not request.doc_content or len(request.doc_content.strip()) <= 20:
        return None
    doc_label = request.doc_id or request.active_file or "documento-activo"
    heading_match = re.match(r'^#[ \t]+([^\r\n]+)$', request.doc_content, re.MULTILINE)
    title = heading_match.group(1).strip() if heading_match else None
    return DocumentContext(
        doc_id=doc_label,
        filename=request.active_file,
        title=title,
        content=request.doc_content,
        content_type="frontend",
    )


def _latest_document() -> Optional[DocumentContext]:
    latest = db.transcriptions.find_one({"is_deleted": {"$ne": True}}, sort=[("ingested_at", -1)])
    if not latest:
        latest = db.transcriptions.find_one({"is_deleted": {"$ne": True}}, sort=[("_id", -1)])
    return load_document_context(str(latest["_id"])) if latest else None


def _requested_document(request: ChatRequest) -> Optional[DocumentContext]:
    document = _frontend_document(request)
    if document:
        logger.info("Using pre-loaded doc_content from frontend (bypassing DB lookup)")
        return document
    if request.doc_id:
        logger.info("Loading document by identifier")
        return load_document_context(request.doc_id)
    if request.active_file:
        logger.info("Loading document by deprecated filename lookup")
        return load_document_by_filename(request.active_file)
    logger.info("No document specified, loading most recent")
    return _latest_document()


@router.post("/stream", responses={400: {"description": "No user message found"}, 500: {"description": "Error en chat"}})
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
        
        document: Optional[DocumentContext] = _requested_document(request)
        
        if not document:
            # Create a minimal context
            document = DocumentContext(
                doc_id="none",
                filename=None,
                title="Sin documento",
                content="No hay documentos disponibles. Por favor graba una transcripción primero.",
                content_type="empty"
            )
        
        logger.info("Chat request prepared; content_type=%s", document.content_type)
        
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
        logger.exception("Error in chat endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ChatResponse, responses={400: {"description": "No user message found"}, 500: {"description": "Error en chat"}})
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
