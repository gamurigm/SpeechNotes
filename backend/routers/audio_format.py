"""
API Router for Audio Formatter
Handles format conversion requests and WebSocket progress streaming
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import asyncio

from services.audio.audio_formatter import AudioFormatterService

try:
    from backend.utils.auth import require_auth
except Exception:
    from ..utils.auth import require_auth

router = APIRouter()

# Initialize formatter service
def get_project_root():
    """Determine project root by locating the backend directory"""
    current_path = Path(__file__).resolve()
    project_root = current_path.parent.parent.parent
    
    if not (project_root / "backend").exists():
        project_root = Path.cwd()
        if not (project_root / "backend").exists():
            raise RuntimeError(f"Could not find project root")
    
    return project_root

try:
    project_root = get_project_root()
except RuntimeError as e:
    print(f"WARNING: {e}")
    project_root = Path.cwd()

print(f"[INIT] Audio Format Router - Project root: {project_root.absolute()}")

audio_formatter = AudioFormatterService(project_root)


# ==================== Request/Response Models ====================

class DetectFormatRequest(BaseModel):
    """Request to detect audio format"""
    file_path: str


class DetectFormatResponse(BaseModel):
    """Response with audio format information"""
    format: str
    codec: str
    sample_rate: int
    channels: int
    bit_depth: int
    duration_seconds: float
    file_size_mb: float
    is_optimized: bool
    is_transcription_ready: bool


class ConvertFileRequest(BaseModel):
    """Request to convert a single file"""
    input_path: str
    output_format: str = "wav"
    profile: str = "transcription"
    custom_params: Optional[Dict] = None
    backup_original: bool = True


class BatchConvertRequest(BaseModel):
    """Request to convert multiple files"""
    files: List[str]
    output_format: str = "wav"
    profile: str = "transcription"
    max_concurrent: int = 3


class JobResponse(BaseModel):
    """Response for job creation"""
    job_id: str
    total_files: int
    status: str
    ws_url: str


class ProfileInfo(BaseModel):
    """Information about a conversion profile"""
    name: str
    description: str
    settings: Dict


# ==================== API Endpoints ====================

@router.get("/profiles", response_model=List[ProfileInfo])
async def get_available_profiles(api_ok: bool = Depends(require_auth)):
    """
    Get list of available conversion profiles
    """
    try:
        profiles = audio_formatter.get_available_profiles()
        return profiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profiles: {str(e)}")


@router.post("/detect", response_model=DetectFormatResponse)
async def detect_audio_format(request: DetectFormatRequest, api_ok: bool = Depends(require_auth)):
    """
    Detect audio format and extract metadata
    """
    try:
        file_path = project_root / request.file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        metadata = audio_formatter.detect_format(file_path)
        
        return DetectFormatResponse(
            format=metadata.format,
            codec=metadata.codec,
            sample_rate=metadata.sample_rate,
            channels=metadata.channels,
            bit_depth=metadata.bit_depth,
            duration_seconds=metadata.duration_seconds,
            file_size_mb=metadata.file_size_mb,
            is_optimized=metadata.is_optimized,
            is_transcription_ready=metadata.is_transcription_ready
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting format: {str(e)}")


@router.post("/convert")
async def convert_single_file(request: ConvertFileRequest, api_ok: bool = Depends(require_auth)):
    """
    Convert a single audio file
    """
    try:
        input_path = project_root / request.input_path
        
        if not input_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.input_path}")
        
        result = await audio_formatter.convert_file(
            input_path=input_path,
            output_format=request.output_format,
            profile=request.profile,
            custom_params=request.custom_params,
            backup_original=request.backup_original
        )
        
        if result.status == "failed":
            raise HTTPException(status_code=500, detail=result.error_message)
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting file: {str(e)}")


@router.post("/batch", response_model=JobResponse)
async def batch_convert_files(request: BatchConvertRequest, api_ok: bool = Depends(require_auth)):
    """
    Start a batch conversion job
    Returns job_id and WebSocket URL for progress updates
    """
    try:
        if not request.files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Validate all files exist
        for file_path_str in request.files:
            file_path = project_root / file_path_str
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {file_path_str}")
        
        # Create job
        job_id = audio_formatter.create_job(
            files=request.files,
            output_format=request.output_format,
            profile=request.profile
        )
        
        # Start job in background
        asyncio.create_task(run_batch_job_background(job_id, request.max_concurrent))
        
        return JobResponse(
            job_id=job_id,
            total_files=len(request.files),
            status="processing",
            ws_url=f"/ws/{job_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting batch job: {str(e)}")


@router.get("/job/{job_id}")
async def get_job_status(job_id: str, api_ok: bool = Depends(require_auth)):
    """
    Get current status of a format job
    """
    job = audio_formatter.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_files": job.total_files,
        "successful": job.successful,
        "failed": job.failed,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "results": [r.to_dict() for r in job.results]
    }


@router.websocket("/ws/{job_id}")
async def format_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for streaming format progress
    Clients connect here to receive real-time updates
    """
    # Log incoming websocket connection
    try:
        scope = websocket.scope
        headers = {k.decode(): v.decode() for k, v in scope.get('headers', [])}
        origin = headers.get('origin') or headers.get('Origin')
        print(f"[WS] Audio format connection for job {job_id} - origin={origin}")
    except Exception as e:
        print(f"[WS] Error reading websocket scope headers: {e}")

    await websocket.accept()
    
    try:
        job = audio_formatter.get_job(job_id)
        
        if not job:
            await websocket.send_json({"error": "Job not found"})
            await websocket.close()
            return
        
        # Stream progress updates
        async for progress in audio_formatter.batch_convert(job_id, max_concurrent=3):
            await websocket.send_json(progress.to_dict())
            await asyncio.sleep(0.1)
        
        # Send completion message
        await websocket.send_json({
            "type": "job_completed",
            "job_id": job_id,
            "status": job.status,
            "successful": job.successful,
            "failed": job.failed,
            "total_files": job.total_files
        })
        
    except WebSocketDisconnect:
        print(f"[WS] Client disconnected from job {job_id}")
    except Exception as e:
        print(f"[WS] Error in WebSocket for job {job_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.post("/cleanup")
async def cleanup_temp_files(api_ok: bool = Depends(require_auth)):
    """
    Clean up temporary files
    """
    try:
        audio_formatter.cleanup_temp_files()
        return {"status": "success", "message": "Temporary files cleaned up"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up: {str(e)}")


# ==================== ENDPOINT DE DESCARGA ====================

@router.get("/download/{file_path:path}")
async def download_formatted_file(file_path: str, api_ok: bool = Depends(require_auth)):
    """
    Descarga el archivo de audio formateado directamente a tu computadora
    
    Ejemplo:
        GET /api/audio-format/download/audio/mi_audio_formatted.wav
        
    Resultado:
        El archivo se descarga automáticamente a tu carpeta Downloads
    """
    try:
        # Construir ruta completa del archivo
        full_path = project_root / file_path
        
        # Verificar que el archivo existe
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")
        
        # Verificar que es un archivo (no directorio)
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="La ruta especificada no es un archivo")
        
        # Obtener nombre del archivo
        filename = full_path.name
        
        print(f"[AudioFormat] Descargando archivo: {filename}")
        
        # Retornar archivo para descarga
        return FileResponse(
            path=str(full_path),
            media_type="application/octet-stream",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")


# ==================== ENDPOINTS ADICIONALES DE FFMPEG ====================

@router.post("/normalize")
async def normalize_audio_volume(
    file_path: str,
    target_loudness_db: float = -16.0,
    api_ok: bool = Depends(require_auth)
):
    """
    Normaliza el volumen del audio a un nivel óptimo
    
    Args:
        file_path: Ruta del archivo de audio
        target_loudness_db: Volumen objetivo en dB (-20 a -10 recomendado)
    """
    try:
        input_path = project_root / file_path
        
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        result = await audio_formatter.normalize_audio(
            input_path=input_path,
            target_loudness_db=target_loudness_db
        )
        
        if result.status == "failed":
            raise HTTPException(status_code=500, detail=result.error_message)
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error normalizando audio: {str(e)}")


@router.post("/trim-silence")
async def trim_audio_silence(
    file_path: str,
    silence_thresh_db: int = -40,
    api_ok: bool = Depends(require_auth)
):
    """
    Elimina silencios al inicio y final del audio
    
    Args:
        file_path: Ruta del archivo de audio
        silence_thresh_db: Umbral de silencio en dB (más negativo = más estricto)
    """
    try:
        input_path = project_root / file_path
        
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        result = await audio_formatter.trim_silence(
            input_path=input_path,
            silence_thresh_db=silence_thresh_db
        )
        
        if result.status == "failed":
            raise HTTPException(status_code=500, detail=result.error_message)
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recortando silencios: {str(e)}")


@router.post("/extract-segment")
async def extract_audio_segment(
    file_path: str,
    start_time_seconds: float,
    end_time_seconds: float,
    api_ok: bool = Depends(require_auth)
):
    """
    Extrae un segmento específico del audio
    
    Args:
        file_path: Ruta del archivo de audio
        start_time_seconds: Tiempo de inicio en segundos
        end_time_seconds: Tiempo de fin en segundos
    """
    try:
        input_path = project_root / file_path
        
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        result = await audio_formatter.extract_segment(
            input_path=input_path,
            start_time_seconds=start_time_seconds,
            end_time_seconds=end_time_seconds
        )
        
        if result.status == "failed":
            raise HTTPException(status_code=500, detail=result.error_message)
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo segmento: {str(e)}")


@router.post("/merge")
async def merge_audio_files(
    file_paths: List[str],
    output_filename: Optional[str] = None,
    api_ok: bool = Depends(require_auth)
):
    """
    Une varios archivos de audio en uno solo
    
    Args:
        file_paths: Lista de rutas de archivos a unir
        output_filename: Nombre del archivo de salida (opcional)
    """
    try:
        input_files = [project_root / fp for fp in file_paths]
        
        result = await audio_formatter.merge_files(
            input_files=input_files,
            output_filename=output_filename
        )
        
        if result.status == "failed":
            raise HTTPException(status_code=500, detail=result.error_message)
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uniendo archivos: {str(e)}")


@router.post("/change-speed")
async def change_audio_speed(
    file_path: str,
    speed_factor: float = 1.5,
    api_ok: bool = Depends(require_auth)
):
    """
    Cambia la velocidad del audio
    
    Args:
        file_path: Ruta del archivo de audio
        speed_factor: Factor de velocidad (1.5 = 50% más rápido, 0.5 = 50% más lento)
    """
    try:
        input_path = project_root / file_path
        
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        result = await audio_formatter.change_speed(
            input_path=input_path,
            speed_factor=speed_factor
        )
        
        if result.status == "failed":
            raise HTTPException(status_code=500, detail=result.error_message)
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cambiando velocidad: {str(e)}")


# ==================== Background Tasks ====================

async def run_batch_job_background(job_id: str, max_concurrent: int = 3):
    """
    Background task to run batch conversion job
    Used when job is started without WebSocket connection
    """
    try:
        async for progress in audio_formatter.batch_convert(job_id, max_concurrent):
            # Progress is handled by WebSocket connections
            # This just ensures the job runs
            pass
        
        print(f"[AudioFormat] Batch job {job_id} completed")
        
    except Exception as e:
        print(f"[AudioFormat] Error running job {job_id}: {e}")

