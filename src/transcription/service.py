"""
Transcription Service - Facade Pattern
Orchestrates transcription workflow
"""
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path

from ..core.riva_client import RivaTranscriber
from ..audio.capture import AudioRecorder
from .formatters import OutputFormatter, OutputWriter


class TranscriptionService:
    """
    High-level service for transcription operations
    Facade Pattern: Simplifies complex subsystem interactions
    SRP: Only responsible for orchestrating transcription workflow
    """
    
    def __init__(
        self,
        transcriber: RivaTranscriber,
        formatter: OutputFormatter,
        writer: OutputWriter
    ):
        """
        Initialize transcription service
        
        Args:
            transcriber: Riva transcriber instance
            formatter: Output formatter
            writer: Output writer
        """
        self.transcriber = transcriber
        self.formatter = formatter
        self.writer = writer
    
    def transcribe_audio_file(
        self,
        audio_path: Path,
        language: str = "es",
        output_file: Optional[str] = None
    ) -> Path:
        """
        Transcribe an audio file
        
        Args:
            audio_path: Path to audio file
            language: Language code
            output_file: Optional output filename
            
        Returns:
            Path to output file
        """
        # Read audio file
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Transcribe
        transcript = self.transcriber.offline_transcribe(audio_data, language)
        
        # Format
        metadata = {
            'timestamp': datetime.now(),
            'audio_file': audio_path.name,
            'language': language,
            'duration_seconds': 0,  # Would need to parse from audio
            'title': f'Transcripción: {audio_path.name}'
        }
        
        formatted = self.formatter.format(transcript, metadata)
        
        # Write
        extension = self.formatter.get_file_extension()
        return self.writer.write(formatted, output_file, extension)
    
    def transcribe_recording(
        self,
        recorder: AudioRecorder,
        language: str = "es",
        output_file: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration: float = 0
    ) -> Path:
        """
        Transcribe a recording
        
        Args:
            recorder: Audio recorder (already recorded)
            language: Language code
            output_file: Optional output filename
            start_time: Recording start time
            duration: Recording duration in seconds
            
        Returns:
            Path to output file
        """
        # Get audio data (recorder should have recorded already)
        audio_data = recorder.record()
        
        # Transcribe
        transcript = self.transcriber.offline_transcribe(audio_data, language)
        
        # Format
        metadata = {
            'timestamp': start_time or datetime.now(),
            'audio_file': 'recording.wav',
            'language': language,
            'duration_seconds': duration,
            'title': 'Grabación Transcrita'
        }
        
        formatted = self.formatter.format(transcript, metadata)
        
        # Write
        extension = self.formatter.get_file_extension()
        return self.writer.write(formatted, output_file, extension)
    
    def transcribe_segments(
        self,
        segments: List[Tuple[datetime, str]],
        output_file: Optional[str] = None,
        method: str = "VAD"
    ) -> Path:
        """
        Save pre-transcribed segments
        
        Args:
            segments: List of (timestamp, text) tuples
            output_file: Optional output filename
            method: Detection method used
            
        Returns:
            Path to output file
        """
        metadata = {
            'title': 'Transcripción por Segmentos',
            'method': method
        }
        
        formatted = self.formatter.format(segments, metadata)
        
        extension = self.formatter.get_file_extension()
        return self.writer.write(formatted, output_file, extension)
