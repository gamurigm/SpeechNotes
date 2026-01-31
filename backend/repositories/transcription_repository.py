from typing import List, Optional, Dict
from bson import ObjectId
from src.database import MongoManager
from src.agent.document_generator import DocumentGenerator

class TranscriptionRepository:
    """
    Data Repository for Transcriptions and Segments.
    Implements Repository Pattern (SOLID: SRP, DIP).
    """
    def __init__(self):
        self.db = MongoManager()
        self.generator = DocumentGenerator()

    def get_latest(self) -> Optional[Dict]:
        return self.db.transcriptions.find_one(
            {"processed": True, "is_deleted": {"$ne": True}},
            sort=[("ingested_at", -1)]
        )

    def get_by_id(self, transcription_id: str) -> Optional[Dict]:
        try:
            return self.db.transcriptions.find_one({"_id": ObjectId(transcription_id)})
        except:
            return None

    def list_recent(self, limit: int = 50) -> List[Dict]:
        cursor = self.db.transcriptions.find(
            {"processed": True, "is_deleted": {"$ne": True}}
        ).sort("ingested_at", -1).limit(limit)
        return list(cursor)

    def get_segments(self, transcription_id: ObjectId) -> List[Dict]:
        return list(self.db.segments.find(
            {"transcription_id": transcription_id}
        ).sort("sequence", 1))

    def update_content(self, transcription_id: str, content: str) -> bool:
        result = self.db.transcriptions.update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {"edited_content": content}}
        )
        return result.modified_count > 0

    def delete(self, transcription_id: str) -> bool:
        result = self.db.transcriptions.update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {"is_deleted": True}}
        )
        return result.matched_count > 0

    def save_audio(self, pcm_data: bytes, filename: str) -> str:
        """Save raw PCM as WAV file"""
        from pathlib import Path
        import wave
        
        output_path = Path(f"notas/{filename}")
        output_path.parent.mkdir(exist_ok=True)
        
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(pcm_data)
        return str(output_path)

    def save_transcription_file(self, content: str, filename: str):
        """Save formatted markdown to disk"""
        from pathlib import Path
        output_path = Path(f"notas/{filename}")
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(output_path)

    def post_process_file(self, filepath: str):
        """Run the ingestion, analysis and generation pipeline"""
        from src.agent.transcription_ingestor import TranscriptionIngestor
        from src.agent.transcription_analyzer import TranscriptionAnalyzer
        
        ingestor = TranscriptionIngestor()
        ingestor._ingest_file(filepath)
        
        analyzer = TranscriptionAnalyzer()
        analyzer.analyze_pending()
        
        self.generator.generate_all()

    def search(self, query_str: str, limit_docs: int = 20, limit_segs: int = 30) -> Dict:
        regex_query = {"$regex": query_str, "$options": "i"}
        
        # Search in transcriptions
        docs = self.db.transcriptions.find({
            "is_deleted": {"$ne": True},
            "processed": True,
            "$or": [
                {"formatted_content": regex_query},
                {"filename": regex_query}
            ]
        }).limit(limit_docs)
        
        # Search in segments
        segments = self.db.segments.find({"content": regex_query}).limit(limit_segs)
        
        return {
            "documents": list(docs),
            "segments": list(segments)
        }
