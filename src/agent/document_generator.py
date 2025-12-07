"""
Document Generator Module
Generates professional markdown documents from structured MongoDB data.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from bson import ObjectId
import os
from openai import OpenAI
from src.database import MongoManager


class DocumentGenerator:
    """
    Generates markdown files from MongoDB data.
    """
    
    def __init__(self, output_dir: str = "notas"):
        self.db = MongoManager()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Minimax Client
        self.minimax_key = os.getenv("MINIMAX_API_KEY")
        self.minimax_base = os.getenv("MINIMAX_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.minimax_model = os.getenv("MINIMAX_MODEL_NAME", "minimaxai/minimax-m2")
        
        if self.minimax_key:
            self.client = OpenAI(
                base_url=self.minimax_base,
                api_key=self.minimax_key
            )
        else:
            self.client = None
        
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
        if self.client:
            print(f"[INFO] Generating document with Minimax M2 for {transcription['filename']}...")
            md = self._generate_with_minimax(transcription, topics)
        else:
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

    def _generate_with_minimax(self, metadata: Dict, topics: List[Dict]) -> str:
        """Generate the document using Minimax LLM."""
        # Prepare context
        context = f"Transcripción: {metadata['filename']}\nFecha: {metadata['date']}\n\nContenido:\n"
        for topic in topics:
            context += f"## {topic['title']} ({topic['start_time']})\n"
            # Join content segments
            content_text = "\n".join(topic['content'])
            context += content_text + "\n\n"
            
        prompt = """Actúa como un redactor técnico experto. 
Genera un documento en Markdown bien estructurado y profesional basado en la siguiente transcripción.
El documento debe incluir:
1. Un resumen ejecutivo.
2. Puntos clave detallados organizados por temas.
3. Conclusiones o pasos a seguir si los hay.

Usa formato Markdown profesional (negritas, listas, encabezados).
Mantén el idioma original (Español).
"""

        try:
            completion = self.client.chat.completions.create(
                model=self.minimax_model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                top_p=0.95,
                max_tokens=8192
            )
            
            content = completion.choices[0].message.content
            
            # Add metadata header
            header = f"""---
original: {metadata['filename']}
fecha: {metadata['date']}
generado_con: Minimax M2
fecha_generacion: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
---

"""
            return header + content
            
        except Exception as e:
            print(f"[ERROR] Minimax generation failed: {e}")
            return self._build_markdown(metadata, topics) # Fallback

