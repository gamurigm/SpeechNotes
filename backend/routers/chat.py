from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json

# Import RagService. 
# Assuming running from backend/ directory where services/ is a package.
from services.rag_service import RagService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize service
try:
    rag_service = RagService()
except Exception as e:
    logger.error(f"Failed to initialize RagService: {e}")
    rag_service = None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint compatible with Vercel AI SDK.
    Expects messages array and streams response in SSE format.
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG Service not available")
    
    try:
        # Get the last user message as query
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query = user_messages[-1].content
        
        async def generate():
            try:
                # Stream the RAG response
                # rag_service.chat_stream() is an async generator
                async for chunk in rag_service.chat_stream(query):
                    # Format as Server-Sent Events
                    data = json.dumps({"content": chunk, "done": False})
                    yield f"data: {data}\n\n"
                
                # Send done signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in chat stream: {e}")
                error_data = json.dumps({"error": str(e)})
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
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint for compatibility."""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG Service not available")
    
    try:
        # Get the last user message as query
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        query = user_messages[-1].content
        result = rag_service.chat(query)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index")
async def trigger_indexing(background_tasks: BackgroundTasks):
    """Trigger indexing of documents from MongoDB to Vector Store in background."""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG Service not available")
        
    background_tasks.add_task(rag_service.index_documents_from_mongo)
    return {"message": "Indexing started in background"}
