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
async def run_post_processing(md_path: Path):
    """
    Run ingestion, analysis and generation in background
    """
    try:
        # Ingest into MongoDB
        ingestor = TranscriptionIngestor()
        ingestor._ingest_file(md_path)
        
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
        
        # 2. Process with ffmpeg (Standardize)
        temp_processed = temp_dir / "processed.wav"
        if not process_audio_file(temp_input, temp_processed):
            raise HTTPException(500, "Failed to process audio file with ffmpeg")
            
        # 3. Transcribe
        try:
            # Initialize orchestration components
            env_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
            transcriber = env_factory.create_transcriber()
            formatter = FormatterFactory.create('markdown') # Simple markdown for whole logs
            writer = OutputWriter(Path("notas"))
            
            # Setup service
            service = TranscriptionService(transcriber, formatter, writer)
            
            # Transcription timestamp
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"transcripcion_upload_{timestamp_str}.md"
            
            # Execute transcription (offline mode)
            print(f"[Transcribe File] Starting Riva offline transcription...")
            # Note: TranscriptionService.transcribe_audio_file returns the Path of created file
            md_path = service.transcribe_audio_file(temp_processed, output_file=output_name)
            
            # 4. Schedule post-processing
            background_tasks.add_task(run_post_processing, md_path)
            
            return {
                "status": "success",
                "filename": md_path.name,
                "original_filename": file.filename,
                "message": "Transcription started and processing scheduled"
            }
            
        except Exception as e:
            print(f"[Transcribe File] Riva/Transcription Error: {e}")
            traceback.print_exc()
            raise HTTPException(500, f"Transcription failed: {str(e)}")
            
    finally:
        # Cleanup temp directory (ideally after background task if needed, 
        # but here the background task only needs the MD path which is in 'notas/')
        # However, if we don't delete temp_dir, it will leak.
        # Delaying deletion if possible or just deleting the input file.
        try:
            # shutil.rmtree(temp_dir) # Be careful if background task needs it.
            # In our case, the background task only needs md_path (in /notas).
            # So it's safe to clear temp_dir.
            shutil.rmtree(temp_dir)
        except:
            pass
