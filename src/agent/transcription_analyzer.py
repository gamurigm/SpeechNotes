"""
Transcription Analyzer Module
Analyzes segments in MongoDB to identify topics and structure.
"""

from typing import List, Dict, Any
import logfire

from src.database import MongoManager
from src.llm.nvidia_client import NvidiaInferenceClient


class TranscriptionAnalyzer:
    """
    Analyzes transcription segments to assign topics using LLM.
    """
    
    def __init__(self):
        self.db = MongoManager()
        self.llm = NvidiaInferenceClient()
        
    @logfire.instrument
    def analyze_pending(self) -> int:
        """
        Analyze all transcriptions that haven't been processed.
        
        Returns:
            Number of transcriptions processed
        """
        pending = self.db.transcriptions.find({"processed": False})
        count = 0
        
        for doc in pending:
            print(f"[INFO] Analyzing transcription: {doc['filename']}")
            try:
                self._analyze_transcription(doc["_id"])
                self.db.transcriptions.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"processed": True}}
                )
                count += 1
            except Exception as e:
                print(f"[ERROR] Failed to analyze {doc['filename']}: {e}")
                
        return count
    
    @logfire.instrument
    def _analyze_transcription(self, transcription_id: str):
        """
        Analyze a single transcription.
        """
        # Get all segments sorted by sequence
        segments = list(self.db.segments.find(
            {"transcription_id": transcription_id}
        ).sort("sequence", 1))
        
        if not segments:
            return
            
        # Prepare content for LLM
        full_text = ""
        for seg in segments:
            full_text += f"[{seg['timestamp']}] {seg['content'][:100]}...\n"
            
        # Ask LLM to identify topics and their start timestamps
        topics = self._detect_topics(full_text)
        
        # Apply topics to segments
        self._apply_topics_to_segments(segments, topics)
        
    def _detect_topics(self, text_summary: str) -> List[Dict[str, Any]]:
        """
        Use LLM to detect topics based on timestamps and content summary.
        """
        prompt = f"""Analiza la siguiente estructura de una clase y define los temas principales.
Para cada tema, indica el timestamp de inicio exacto y un título descriptivo.

Estructura (Timestamp y extracto):
{text_summary[:3000]} # Limit to avoid token overflow

Responde SOLO con una lista en este formato:
TIMESTAMP | TÍTULO DEL TEMA
"""
        try:
            response = self.llm.generate(prompt, temperature=0.2, max_tokens=1000)
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"[WARN] LLM analysis failed: {e}")
            if "403" in str(e):
                print("[WARN] Check NVIDIA_API_KEY in .env. It might be invalid, expired, or missing permissions.")
            # Fallback: Single topic
            return [{"timestamp": "00:00:00", "title": "Clase General"}]
            
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured topics."""
        topics = []
        lines = response.strip().split('\n')
        
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    ts = parts[0].strip()
                    title = parts[1].strip()
                    # Validate timestamp format
                    if len(ts) == 8 and ts[2] == ':' and ts[5] == ':':
                        topics.append({"timestamp": ts, "title": title})
                        
        if not topics:
             return [{"timestamp": "00:00:00", "title": "Clase General"}]
             
        # Sort by timestamp
        topics.sort(key=lambda x: x["timestamp"])
        return topics
        
    def _apply_topics_to_segments(self, segments: List[Dict], topics: List[Dict]):
        """
        Update segments in MongoDB with their corresponding topic.
        """
        current_topic_idx = 0
        current_topic = topics[0]
        
        for seg in segments:
            seg_ts = seg["timestamp"]
            
            # Check if we moved to next topic
            if current_topic_idx + 1 < len(topics):
                next_topic = topics[current_topic_idx + 1]
                if seg_ts >= next_topic["timestamp"]:
                    current_topic = next_topic
                    current_topic_idx += 1
            
            # Update segment in DB
            self.db.segments.update_one(
                {"_id": seg["_id"]},
                {"$set": {
                    "topic_title": current_topic["title"]
                }}
            )
