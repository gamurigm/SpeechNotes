"""
API Router for Formatter Agent
Handles formatting requests and WebSocket progress streaming
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import asyncio
import os

from services.agents.formatter_agent import FormatterAgent
try:
    # Prefer importing via package name when backend is on sys.path
    from backend.utils.auth import require_auth
except Exception:
    # Fallback to relative import for package contexts
    from ..utils.auth import require_auth

router = APIRouter()

# Initialize formatter agent
# Get the actual project root by looking for the backend directory
def get_project_root():
    """Determine project root by locating the backend directory"""
    current_path = Path(__file__).resolve()
    # Go up from backend/routers/formatter.py to get to project root
    project_root = current_path.parent.parent.parent
    
    # Verify the structure exists
    if not (project_root / "backend").exists():
        # Fallback: try to find it from current working directory
        project_root = Path.cwd()
        if not (project_root / "backend").exists():
            raise RuntimeError(f"Could not find project root. Checked: {current_path.parent.parent.parent}, {Path.cwd()}")
    
    return project_root

try:
    project_root = get_project_root()
except RuntimeError as e:
    print(f"WARNING: {e}")
    project_root = Path.cwd()

print(f"[INIT] Formatter Router - Project root: {project_root.absolute()}")
print(f"[INIT] Notas directory: {(project_root / 'notas').absolute()}")
print(f"[INIT] Notas exists: {(project_root / 'notas').exists()}")

formatter_agent = FormatterAgent(project_root)


class FormatRequest(BaseModel):
    """Request body for starting a format job"""
    files: List[str]
    output_dir: str = "notas"


class FormatJobResponse(BaseModel):
    """Response for job creation"""
    job_id: str
    total_files: int
    ws_url: str


class FileInfo(BaseModel):
    """Information about an available markdown file"""
    name: str
    path: str
    size: int
    modified: str
    metadata: dict


@router.get("/files", response_model=List[FileInfo])
async def list_available_files(api_ok: bool = Depends(require_auth)):
    """
    List all available markdown files in notas/ directory
    """
    try:
        notas_dir = project_root / "notas"
        
        print(f"\n{'='*60}")
        print(f"[DEBUG] Project root: {project_root}")
        print(f"[DEBUG] Looking for files in: {notas_dir}")
        print(f"[DEBUG] Directory exists: {notas_dir.exists()}")
        print(f"[DEBUG] Absolute path: {notas_dir.absolute()}")
        
        if not notas_dir.exists():
            print(f"[DEBUG] ❌ notas directory does not exist!")
            return []
        
        files_info = []
        all_files = list(notas_dir.glob("*.md"))
        print(f"[DEBUG] Total .md files found: {len(all_files)}")
        
        # Show all files found
        for f in all_files:
            print(f"[DEBUG]   - {f.name}")
        
        for file_path in all_files:
            print(f"\n[DEBUG] Processing: {file_path.name}")
            
            # Skip already formatted files and backups
            if file_path.name.endswith("_formatted.md"):
                print(f"[DEBUG]   ❌ Skipping (already formatted)")
                continue
            if file_path.name.endswith(".original.md"):
                print(f"[DEBUG]   ❌ Skipping (backup)")
                continue
            if ".original" in file_path.name:
                print(f"[DEBUG]   ❌ Skipping (backup variant)")
                continue
            
            print(f"[DEBUG]   ✅ File will be included")
            
            # Get file stats
            stats = file_path.stat()
            
            # Extract metadata from file
            try:
                content = file_path.read_text(encoding='utf-8')
                metadata = {}
                
                # Parse YAML frontmatter
                import re
                yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if yaml_match:
                    yaml_content = yaml_match[1]
                    for line in yaml_content.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
            except:
                metadata = {}
            
            files_info.append(FileInfo(
                name=file_path.name,
                path=f"notas/{file_path.name}",
                size=stats.st_size,
                modified=stats.st_mtime.__str__(),
                metadata=metadata
            ))
        
        print(f"\n[DEBUG] Total files to return: {len(files_info)}")
        for f in files_info:
            print(f"[DEBUG]   - {f.name}")
        print(f"{'='*60}\n")
        return files_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@router.post("/start", response_model=FormatJobResponse)
async def start_format_job(request: FormatRequest, api_ok: bool = Depends(require_auth)):
    """
    Start a new formatting job
    Returns job_id and WebSocket URL for progress updates
    """
    try:
        if not request.files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Create job
        job_id = formatter_agent.create_job(request.files, request.output_dir)
        
        # Start job in background
        asyncio.create_task(run_job_background(job_id))
        
        return FormatJobResponse(
            job_id=job_id,
            total_files=len(request.files),
            # WebSocket endpoint is mounted at /api/format/ws/{job_id}
            # so we return the ws path relative to the router: /ws/{job_id}
            ws_url=f"/ws/{job_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting job: {str(e)}")


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
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
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
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
