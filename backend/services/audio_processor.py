"""
Audio Processor Service
Handles audio chunk processing and transcription using NVIDIA NIM
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import io
import wave
from datetime import datetime
from typing import Optional, Dict
from src.llm.nvidia_client import NvidiaInferenceClient

class AudioProcessor:
    """Process audio chunks and transcribe using NVIDIA NIM"""
    
    def __init__(self):
        self.llm = NvidiaInferenceClient()
        self.audio_buffer = []
        self.start_time = datetime.now()
        self.transcription_buffer = []
        
    async def transcribe_chunk(self, audio_data: bytes) -> Optional[Dict]:
        """
        Transcribe an audio chunk.
        
        Args:
            audio_data: Raw audio bytes from browser
            
        Returns:
            Dict with transcribed text and timestamp
        """
        try:
            # Add to buffer
            self.audio_buffer.append(audio_data)
            
            # For now, simulate transcription
            # In production, you would:
            # 1. Convert audio_data to proper format
            # 2. Send to Whisper API or NVIDIA NIM audio model
            # 3. Return transcribed text
            
            # Placeholder: Return mock transcription
            elapsed = (datetime.now() - self.start_time).total_seconds()
            timestamp = self._format_timestamp(elapsed)
            
            # TODO: Integrate with actual Whisper API
            # For now, return a placeholder
            text = f"[Transcription chunk at {timestamp}]"
            
            result = {
                "text": text,
                "timestamp": timestamp
            }
            
            self.transcription_buffer.append(result)
            return result
            
        except Exception as e:
            print(f"[AudioProcessor] Error transcribing chunk: {e}")
            return None
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    async def finalize(self):
        """Finalize and save the complete transcription"""
        try:
            # Combine all transcription chunks
            full_text = "\n\n".join([t["text"] for t in self.transcription_buffer])
            
            # Save to MongoDB using existing ingestor
            from src.agent.transcription_ingestor import TranscriptionIngestor
            from src.database import MongoManager
            from pathlib import Path
            
            # Create a temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcripcion_{timestamp}.md"
            temp_path = Path(f"notas/{filename}")
            
            # Write content
            temp_path.parent.mkdir(exist_ok=True)
            temp_path.write_text(full_text, encoding='utf-8')
            
            # Ingest into MongoDB
            db = MongoManager()
            ingestor = TranscriptionIngestor()
            ingestor._ingest_file(temp_path)
            
            print(f"[AudioProcessor] Saved transcription: {filename}")
            
        except Exception as e:
            print(f"[AudioProcessor] Error finalizing: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        self.audio_buffer.clear()
        self.transcription_buffer.clear()
