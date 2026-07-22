"""
API Router for Formatter Agent
Handles formatting requests and WebSocket progress streaming
Content is read from and written to the database (no file I/O).
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import Annotated, List, Optional
from pathlib import Path
import asyncio
import os

from services.agents.formatter_agent import FormatterAgent
from src.database.mongo_manager import MongoManager
try:
    from backend.utils.auth import require_auth
except Exception:
    from ..utils.auth import require_auth

router = APIRouter()

formatter_agent = FormatterAgent(Path.cwd())


class FormatRequest(BaseModel):
    """Request body for starting a format job using transcription IDs"""
    file_ids: List[str]


class FormatJobResponse(BaseModel):
    """Response for job creation"""
    job_id: str
    total_files: int
    ws_url: str


class FileInfo(BaseModel):
    """Information about an available transcription from the database"""
    id: str
    name: str
    fecha: str
    palabras: str
    tipo: str
    tiene_contenido: bool
    ya_formateado: bool


@router.get("/files", response_model=List[FileInfo])
async def list_available_files(api_ok: Annotated[bool, Depends(require_auth)]):
    """
    List all available transcriptions from the database that can be formatted.
    """
    try:
        db = MongoManager()
        docs = db.transcriptions.find({
            "is_deleted": {"$ne": True}
        }).sort("ingested_at", -1).limit(100)
        
        files_info = []
        for doc in docs:
            doc_id = doc.get("_id", "")
            raw = doc.get("raw_content", "")
            edited = doc.get("edited_content", "")
            formatted = doc.get("formatted_content", "")
            
            files_info.append(FileInfo(
                id=str(doc_id),
                name=doc.get("filename", f"doc_{doc_id}"),
                fecha=doc.get("date", "N/A"),
                palabras=str(doc.get("word_count", "N/A")),
                tipo=doc.get("source_type", "desconocido"),
                tiene_contenido=bool(raw or edited),
                ya_formateado=bool(formatted) or doc.get("is_formatted", False)
            ))
        
        return files_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing transcriptions: {str(e)}")


@router.post("/start", response_model=FormatJobResponse)
async def start_format_job(request: FormatRequest, api_ok: Annotated[bool, Depends(require_auth)]):
    """
    Start a new formatting job using transcription IDs from the database.
    """
    try:
        if not request.file_ids:
            raise HTTPException(status_code=400, detail="No file IDs provided")
        
        job_id = formatter_agent.create_job(request.file_ids)
        
        return FormatJobResponse(
            job_id=job_id,
            total_files=len(request.file_ids),
            ws_url=f"/ws/{job_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting job: {str(e)}")


@router.get("/job/{job_id}")
async def get_job_status(job_id: str, api_ok: Annotated[bool, Depends(require_auth)]):
    """
    Get current status of a formatting job
    """
    job = formatter_agent.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_files": len(job.files),
        "successful": job.successful,
        "failed": job.failed,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "progress": [p.to_dict() for p in job.progress]
    }


@router.websocket("/ws/{job_id}")
async def format_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for streaming format progress
    Clients connect here to receive real-time updates
    """
    # Log incoming websocket scope for debugging (origin, headers)
    try:
        scope = websocket.scope
        headers = {k.decode(): v.decode() for k, v in scope.get('headers', [])}
        origin = headers.get('origin') or headers.get('Origin')
        print(f"[WS] Incoming connection for job {job_id} - origin={origin} - headers={headers}")
    except Exception as e:
        print(f"[WS] Error reading websocket scope headers: {e}")

    await websocket.accept()
    
    try:
        job = formatter_agent.get_job(job_id)
        
        if not job:
            await websocket.send_json({"error": "Job not found"})
            await websocket.close()
            return
        
        # Stream progress updates
        async for progress in formatter_agent.run_job(job_id):
            await websocket.send_json(progress.to_dict())
            await asyncio.sleep(0.1)  # Small delay to avoid overwhelming client
        
        # Send completion message
        await websocket.send_json({
            "status": "job_completed",
            "job_id": job_id,
            "successful": job.successful,
            "failed": job.failed
        })
        
    except WebSocketDisconnect:
        print(f"Client disconnected from job {job_id}")
    except Exception as e:
        print(f"Error in WebSocket for job {job_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def run_job_background(job_id: str):
    """
    Background task to run formatting job
    Used when job is started without WebSocket connection
    """
    try:
        async for progress in formatter_agent.run_job(job_id):
            # Progress is handled by WebSocket connections
            # This just ensures the job runs
            pass
    except Exception as e:
        print(f"Error running job {job_id}: {e}")
