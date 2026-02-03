"""
Router for file-based transcription
Handles audio file upload, conversion with ffmpeg, and transcription
"""

import os
import shutil
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional
import logfire

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydub import AudioSegment

from src.core.environment_factory import TranscriptionEnvironmentFactoryProvider
from src.transcription import FormatterFactory, OutputWriter, TranscriptionService
from src.database import MongoManager
from src.agent.transcription_ingestor import TranscriptionIngestor
from src.agent.transcription_analyzer import TranscriptionAnalyzer
from src.agent.document_generator import DocumentGenerator

router = APIRouter()

@logfire.instrument
def process_audio_file(input_path: Path, output_path: Path):
    """
    Standardize audio file using ffmpeg (via pydub)
    Ensures 16kHz, mono, PCM for Riva
    """
    try:
        # Load any audio format supported by ffmpeg
        audio = AudioSegment.from_file(str(input_path))
        
        # Standardize for Riva: 16kHz, mono, 16-bit
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # Save as WAV for transcription
        audio.export(str(output_path), format="wav")
        return True
    except Exception as e:
        print(f"[FFMPEG] Error processing audio: {e}")
        return False

@logfire.instrument
async def run_post_processing(md_path: Path, source_type: str = "live_recording", source_filename: str = None):
    """
    Run ingestion, analysis and generation in background
    
    Args:
        md_path: Path to the markdown file
        source_type: Either "live_recording" or "uploaded_file"
        source_filename: Original filename if uploaded
    """
    try:
        # Ingest into MongoDB with source metadata
        ingestor = TranscriptionIngestor()
        ingestor._ingest_file(md_path, source_type=source_type, source_filename=source_filename)
        
        # Analysis (Logfire, summaries, etc)
        analyzer = TranscriptionAnalyzer()
        analyzer.analyze_pending()
        
        # Document generation
        generator = DocumentGenerator()
        generator.generate_all()
        
        print(f"[Batch Post] Completed post-processing for {md_path.name}")
    except Exception as e:
        print(f"[Batch Post] Error: {e}")
        traceback.print_exc()

@logfire.instrument
async def full_transcription_pipeline(file_path: Path, output_name: str, temp_dir: Path, original_filename: str = None):
    """
    Background job: Standardize audio -> Transcribe -> Post-process
    
    Args:
        file_path: Path to the uploaded audio file
        output_name: Name for the output markdown file
        temp_dir: Temporary directory for processing
        original_filename: Original name of the uploaded file
    """
    try:
        # 1. Standardize with ffmpeg
        temp_processed = temp_dir / "processed.wav"
        print(f"[Worker] Processing audio: {file_path.name}")
        if not process_audio_file(file_path, temp_processed):
            print(f"[Worker] ❌ Failed to process audio with ffmpeg")
            return

        # 2. Transcribe
        env_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
        transcriber = env_factory.create_transcriber()
        formatter = FormatterFactory.create('markdown')
        writer = OutputWriter(Path("notas"))
        service = TranscriptionService(transcriber, formatter, writer)

        print(f"[Worker] Starting transcription for {output_name}...")
        md_path = service.transcribe_audio_file(temp_processed, output_file=output_name)
        
        # 2.5. Add header to markdown file indicating it's from uploaded file
        if md_path.exists() and original_filename:
            content = md_path.read_text(encoding='utf-8')
            header = f"""---
**📁 Transcripción de Archivo Subido**  
📄 Archivo Original: `{original_filename}`  
📅 Fecha de Procesamiento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
🤖 Motor: NVIDIA Riva + FFmpeg

---

"""
            md_path.write_text(header + content, encoding='utf-8')
            print(f"[Worker] ✅ Added upload metadata header to {md_path.name}")

        # 3. Batch Post-processing with source metadata
        await run_post_processing(md_path, source_type="uploaded_file", source_filename=original_filename)
        print(f"[Worker] ✅ All background tasks completed for {output_name}")

    except Exception as e:
        print(f"[Worker] ❌ Pipeline error: {e}")
        traceback.print_exc()
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

@router.post("/transcribe-file")
@logfire.instrument
async def transcribe_uploaded_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Endpoint for uploading and transcribing an audio file
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # 1. Save upload to temp
        input_ext = Path(file.filename).suffix or ".audio"
        temp_input = temp_dir / f"upload_{datetime.now().strftime('%H%M%S')}{input_ext}"
        
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"[Transcribe File] Received: {file.filename} -> {temp_input}")
        
        # 2. Prepare metadata
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"transcripcion_upload_{timestamp_str}.md"
        
        # 3. Schedule the WHOLE pipeline as a background task with original filename
        background_tasks.add_task(
            full_transcription_pipeline, 
            temp_input, 
            output_name, 
            temp_dir,
            file.filename  # Pass original filename for metadata
        )
        
        return {
            "status": "success",
            "filename": output_name,
            "original_filename": file.filename,
            "message": "Upload successful. Background processing started."
        }
            
    except Exception as e:
        print(f"[Transcribe File] Error: {e}")
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        raise HTTPException(500, f"Failed to start background transcription: {str(e)}")
