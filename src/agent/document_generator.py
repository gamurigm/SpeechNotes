"""
Document Generator Module
Generates professional markdown documents from structured MongoDB data.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from bson import ObjectId
from src.database import MongoManager


class DocumentGenerator:
    """
    Generates markdown files from MongoDB data.
    """
    
    def __init__(self, output_dir: str = "knowledge_base/transcriptions"):
        self.db = MongoManager()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_all(self) -> int:
        """
        Generate markdown for all processed transcriptions.
        
        Returns:
            Number of documents generated
        """
        processed = self.db.transcriptions.find({"processed": True})
        count = 0
        
        for doc in processed:
            try:
                self._generate_document(doc)
                count += 1
            except Exception as e:
                print(f"[ERROR] Failed to generate document for {doc['filename']}: {e}")
                
        return count
    
    def _generate_document(self, transcription: Dict[str, Any]):
        """
        Generate a single markdown document.
        """
        # Get segments sorted by sequence
        segments = list(self.db.segments.find(
            {"transcription_id": transcription["_id"]}
        ).sort("sequence", 1))
        
        if not segments:
            return
            
        # Group by topic
        topics = self._group_by_topic(segments)
        
        # Build Markdown
        md = self._build_markdown(transcription, topics)
        
        # Save file
        filename = transcription["filename"].replace("transcripcion_", "processed_")
        if not filename.startswith("processed_"):
            filename = f"processed_{filename}"
            
        output_path = self.output_dir / filename
        output_path.write_text(md, encoding='utf-8')
        print(f"[INFO] Generated document: {output_path}")
        
    def _group_by_topic(self, segments: List[Dict]) -> List[Dict[str, Any]]:
        """Group segments by their assigned topic."""
        topics = []
        current_topic = None
        
        for seg in segments:
            topic_title = seg.get("topic_title", "General")
            
            if current_topic is None or current_topic["title"] != topic_title:
                if current_topic:
                    topics.append(current_topic)
                
                current_topic = {
                    "title": topic_title,
                    "start_time": seg["timestamp"],
                    "content": []
                }
            
            current_topic["content"].append(seg["content"])
            
        if current_topic:
            topics.append(current_topic)
            
        return topics
        
    def _build_markdown(self, metadata: Dict, topics: List[Dict]) -> str:
        """Build the markdown string."""
        topic_titles = [t["title"] for t in topics]
        
        md = f"""---
original: {metadata['filename']}
fecha: {metadata['date']}
hora_inicio: {metadata['time']}
palabras: {metadata.get('word_count', 0):,}
temas: {topic_titles}
generado: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
---

# Transcripción: {metadata['date']}
**Duración**: {metadata.get('duration', 'N/A')} | **Palabras**: {metadata.get('word_count', 0):,}

## 📋 Tabla de Contenidos
"""
        
        # Table of Contents
        for i, topic in enumerate(topics, 1):
            anchor = topic["title"].lower().replace(" ", "-").replace(",", "")
            md += f"{i}. [{topic['title']}](#tema-{i}-{anchor})\n"
            
        md += "\n---\n\n"
        
        # Topics Content
        for i, topic in enumerate(topics, 1):
            anchor = topic["title"].lower().replace(" ", "-").replace(",", "")
            md += f"## Tema {i}: {topic['title']}\n"
            md += f"**⏱️ Inicio**: {topic['start_time']}\n\n"
            
            # Join segments preserving original text
            full_text = "\n\n".join(topic["content"])
            md += full_text + "\n\n"
            
            md += "---\n\n"
            
        return md
