"""
Transcription Ingestor Module
Loads raw markdown transcriptions into MongoDB.
"""

import re
import logfire
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pymongo.errors import DuplicateKeyError

from src.database import MongoManager


class TranscriptionIngestor:
    """
    Ingests transcription files into MongoDB.
    """
    
    def __init__(self, source_dir: str = "notas"):
        self.source_dir = Path(source_dir)
        self.db = MongoManager()
        
    @logfire.instrument
    def ingest_all(self) -> Dict[str, int]:
        """
        Ingest all files from source directory.
        
        Returns:
            Stats of ingestion (added, skipped, errors)
        """
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")
            
        files = list(self.source_dir.glob("transcripcion_*.md"))
        files.extend(self.source_dir.glob("mi_audio_*.md"))
        
        stats = {"added": 0, "skipped": 0, "errors": 0}
        
        print(f"[INFO] Found {len(files)} files to ingest")
        
        for file_path in files:
            try:
                if self._ingest_file(file_path):
                    stats["added"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                print(f"[ERROR] Failed to ingest {file_path.name}: {e}")
                stats["errors"] += 1
                
        return stats
    
    @logfire.instrument
    def _ingest_file(self, file_path: Path, source_type: str = "live_recording", source_filename: str = None) -> bool:
        """
        Ingest a single file.
        
        Args:
            file_path: Path to the markdown file (Path or str)
            source_type: Either "live_recording" or "uploaded_file"
            source_filename: Original filename if uploaded
        
        Returns:
            True if added, False if skipped (already exists)
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        # Check if already exists
        existing = self.db.transcriptions.find_one({"filename": file_path.name})
        if existing:
            return False
            
        # Extract metadata
        metadata = self._extract_metadata(file_path)
        content = file_path.read_text(encoding='utf-8')
        
        # Create transcription document
        transcription_doc = {
            "filename": file_path.name,
            "raw_content": content,
            "date": metadata["date"],
            "time": metadata["time"],
            "word_count": metadata["word_count"],
            "source_type": source_type,  # NEW: Track origin
            "source_filename": source_filename,  # NEW: Original uploaded filename
            "processed": False,
            "ingested_at": datetime.now()
        }
        
        # Insert transcription
        result = self.db.transcriptions.insert_one(transcription_doc)
        transcription_id = result.inserted_id
        
        # Initial segmentation (by timestamps)
        segments = self._initial_segmentation(content, transcription_id)
        
        if segments:
            self.db.segments.insert_many(segments)
            
        print(f"[INFO] Ingested {file_path.name} ({source_type}) with {len(segments)} initial segments")
        return True
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from filename and content."""
        filename = file_path.name
        
        # Extract date/time from filename
        match = re.search(r'(\d{8})_(\d{6})', filename)
        if match:
            date_str, time_str = match.groups()
            try:
                date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
                time = datetime.strptime(time_str, "%H%M%S").strftime("%H:%M:%S")
            except ValueError:
                mtime = file_path.stat().st_mtime
                dt = datetime.fromtimestamp(mtime)
                date = dt.strftime("%Y-%m-%d")
                time = dt.strftime("%H:%M:%S")
        else:
            mtime = file_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            date = dt.strftime("%Y-%m-%d")
            time = dt.strftime("%H:%M:%S")
            
        # Word count
        try:
            content = file_path.read_text(encoding='utf-8')
            word_count = len(content.split())
        except:
            word_count = 0
            
        return {
            "date": date,
            "time": time,
            "word_count": word_count
        }
        
    def _initial_segmentation(self, content: str, transcription_id: Any) -> List[Dict[str, Any]]:
        """
        Split content by timestamps for initial segments.
        These segments will be refined by the Analyzer later.
        """
        segments = []
        
        # Split by timestamp patterns (**HH:MM:SS** or [HH:MM:SS])
        parts = re.split(r'(\*\*\d{2}:\d{2}:\d{2}\*\*|\[\d{2}:\d{2}:\d{2}\])', content)
        
        current_timestamp = "00:00:00"
        sequence = 1
        
        # If content starts with text before first timestamp
        if parts[0].strip():
            segments.append({
                "transcription_id": transcription_id,
                "timestamp": current_timestamp,
                "content": parts[0].strip(),
                "sequence": sequence,
                "topic_title": None, # To be filled by Analyzer
                "topic_summary": None
            })
            sequence += 1
            
        # Process parts (timestamp, content, timestamp, content...)
        for i in range(1, len(parts), 2):
            timestamp_raw = parts[i]
            text = parts[i+1] if i+1 < len(parts) else ""
            
            # Clean timestamp
            ts_match = re.search(r'(\d{2}:\d{2}:\d{2})', timestamp_raw)
            if ts_match:
                current_timestamp = ts_match.group(1)
                
            if text.strip():
                segments.append({
                    "transcription_id": transcription_id,
                    "timestamp": current_timestamp,
                    "content": text.strip(),
                    "sequence": sequence,
                    "topic_title": None,
                    "topic_summary": None
                })
                sequence += 1
                
        return segments
