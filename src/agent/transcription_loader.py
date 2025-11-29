"""
Transcription Loader Module
Loads and processes transcription files from notas/ directory.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TranscriptionLoader:
    """
    Loads transcription files and processes them into professional markdown format.
    """
    
    def __init__(
        self,
        source_dir: str = "notas",
        processed_dir: str = "knowledge_base/transcriptions"
    ):
        """
        Initialize the transcription loader.
        
        Args:
            source_dir: Directory containing original transcriptions
            processed_dir: Directory for processed transcriptions
        """
        self.source_dir = Path(source_dir)
        self.processed_dir = Path(processed_dir)
        
        # Ensure processed directory exists
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def load_from_directory(self) -> List[Path]:
        """
        Load all transcription files from source directory.
        
        Returns:
            List of paths to transcription files
        """
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")
        
        # Find all .md files
        transcription_files = list(self.source_dir.glob("transcripcion_*.md"))
        transcription_files.extend(self.source_dir.glob("mi_audio_*.md"))
        
        return sorted(transcription_files)
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from transcription filename and content.
        
        Args:
            file_path: Path to transcription file
            
        Returns:
            Dictionary with metadata
        """
        filename = file_path.name
        
        # Extract date and time from filename
        # Format: transcripcion_YYYYMMDD_HHMMSS.md
        match = re.search(r'(\d{8})_(\d{6})', filename)
        
        if match:
            date_str, time_str = match.groups()
            try:
                date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
                time = datetime.strptime(time_str, "%H%M%S").strftime("%H:%M:%S")
            except ValueError:
                # Fallback to file modification time
                mtime = file_path.stat().st_mtime
                dt = datetime.fromtimestamp(mtime)
                date = dt.strftime("%Y-%m-%d")
                time = dt.strftime("%H:%M:%S")
        else:
            # Fallback to file modification time
            mtime = file_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            date = dt.strftime("%Y-%m-%d")
            time = dt.strftime("%H:%M:%S")
        
        # Read file to get word count
        try:
            content = file_path.read_text(encoding='utf-8')
            word_count = len(content.split())
            
            # Count segments (lines starting with timestamp pattern)
            segments = len(re.findall(r'\*\*\d{2}:\d{2}:\d{2}\*\*', content))
            if segments == 0:
                # Alternative pattern
                segments = len(re.findall(r'\[\d{2}:\d{2}:\d{2}\]', content))
            if segments == 0:
                # Default to 1 if no timestamps found
                segments = 1
        except Exception as e:
            print(f"   ⚠️ Error reading file: {e}")
            content = ""
            word_count = 0
            segments = 1
        
        return {
            "filename": filename,
            "date": date,
            "time": time,
            "word_count": word_count,
            "segment_count": segments,
            "type": "transcription",
            "file_size": file_path.stat().st_size
        }
    
    def detect_topics(self, content: str) -> List[Dict[str, Any]]:
        """
        Detect topic changes in transcription using NVIDIA NIM.
        
        Args:
            content: Transcription content
            
        Returns:
            List of topics with timestamps and content
        """
        from src.llm.nvidia_client import NvidiaInferenceClient
        
        # Initialize client
        client = NvidiaInferenceClient()
        
        # Prepare prompt for topic detection
        prompt = f"""Analiza la siguiente transcripción de clase y divide el contenido en temas principales.
Para cada tema, identifica:
1. Título del tema (conciso, máximo 6 palabras)
2. Timestamp aproximado de inicio
3. Puntos clave (3-5 bullets)

Transcripción:
{content[:4000]}  # Limit to avoid token limits

Responde en formato:
TEMA: [Título]
TIMESTAMP: [HH:MM:SS]
PUNTOS:
- Punto 1
- Punto 2
---"""
        
        try:
            response = client.generate(prompt, temperature=0.3, max_tokens=2000)
            
            # Parse response to extract topics
            topics = self._parse_topic_response(response, content)
            
            return topics if topics else self._fallback_segmentation(content)
        
        except Exception as e:
            print(f"[WARN] Error detecting topics with AI: {e}")
            print("   Using fallback segmentation...")
            return self._fallback_segmentation(content)
    
    def _parse_topic_response(self, response: str, content: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract topics."""
        topics = []
        
        # Split by topic markers
        topic_blocks = re.split(r'---+', response)
        
        for block in topic_blocks:
            if not block.strip():
                continue
            
            # Extract title
            title_match = re.search(r'TEMA:\s*(.+)', block)
            timestamp_match = re.search(r'TIMESTAMP:\s*(\d{2}:\d{2}:\d{2})', block)
            
            if title_match:
                title = title_match.group(1).strip()
                timestamp = timestamp_match.group(1) if timestamp_match else "00:00:00"
                
                # Extract key points
                points = []
                for line in block.split('\n'):
                    if line.strip().startswith('-'):
                        points.append(line.strip()[1:].strip())
                
                topics.append({
                    "title": title,
                    "timestamp_start": timestamp,
                    "key_points": points,
                    "content": ""  # Will be filled later
                })
        
        return topics
    
    def _fallback_segmentation(self, content: str) -> List[Dict[str, Any]]:
        """
        Fallback segmentation when AI detection fails.
        Segments by timestamp markers in the content.
        """
        topics = []
        
        # Split by timestamp patterns
        segments = re.split(r'(\*\*\d{2}:\d{2}:\d{2}\*\*|\[\d{2}:\d{2}:\d{2}\])', content)
        
        current_topic = None
        current_content = []
        
        for i, segment in enumerate(segments):
            # Check if it's a timestamp
            timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2})', segment)
            
            if timestamp_match:
                # Save previous topic
                if current_topic:
                    current_topic["content"] = "\n".join(current_content).strip()
                    topics.append(current_topic)
                
                # Start new topic
                current_topic = {
                    "title": f"Segmento {len(topics) + 1}",
                    "timestamp_start": timestamp_match.group(1),
                    "key_points": [],
                    "content": ""
                }
                current_content = []
            else:
                current_content.append(segment)
        
        # Add last topic
        if current_topic:
            current_topic["content"] = "\n".join(current_content).strip()
            topics.append(current_topic)
        
        # If no topics found, create one topic with all content
        if not topics:
            topics.append({
                "title": "Transcripción Completa",
                "timestamp_start": "00:00:00",
                "key_points": [],
                "content": content
            })
        
        return topics
    
    def segment_by_topics(self, content: str, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segment content by detected topics.
        
        Args:
            content: Full transcription content
            topics: List of detected topics
            
        Returns:
            Topics with content filled in
        """
        # If topics already have content, return as is
        if topics and topics[0].get("content"):
            return topics
        
        # Otherwise, split content by timestamps
        for i, topic in enumerate(topics):
            start_time = topic["timestamp_start"]
            
            # Find content between this timestamp and next
            if i < len(topics) - 1:
                next_time = topics[i + 1]["timestamp_start"]
                # Extract content between timestamps
                pattern = f"{start_time}.*?(?={next_time})"
            else:
                # Last topic - get everything after timestamp
                pattern = f"{start_time}.*"
            
            match = re.search(pattern, content, re.DOTALL)
            if match:
                topic["content"] = match.group(0).strip()
        
        return topics
    
    def format_professional_md(
        self,
        metadata: Dict[str, Any],
        topics: List[Dict[str, Any]],
        original_path: Path
    ) -> str:
        """
        Format transcription as professional markdown.
        
        Args:
            metadata: Transcription metadata
            topics: List of topics with content
            original_path: Path to original file
            
        Returns:
            Formatted markdown string
        """
        # Build frontmatter
        topic_titles = [t["title"] for t in topics]
        
        md = f"""---
original: {original_path.resolve().relative_to(Path.cwd())}
fecha: {metadata['date']}
hora_inicio: {metadata['time']}
palabras: {metadata['word_count']:,}
segmentos: {len(topics)}
temas: {topic_titles}
procesado: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
---

# Transcripción: Clase
**Fecha**: {metadata['date']} | **Palabras**: {metadata['word_count']:,}

## 📋 Tabla de Contenidos
"""
        
        # Add table of contents
        for i, topic in enumerate(topics, 1):
            anchor = topic["title"].lower().replace(" ", "-").replace(",", "")
            md += f"{i}. [{topic['title']}](#tema-{i}-{anchor})\n"
        
        md += "\n---\n\n"
        
        # Add topics
        for i, topic in enumerate(topics, 1):
            anchor = topic["title"].lower().replace(" ", "-").replace(",", "")
            md += f"## Tema {i}: {topic['title']}\n"
            md += f"**⏱️ Timestamp**: {topic['timestamp_start']}\n\n"
            
            # Add content
            if topic["content"]:
                md += topic["content"] + "\n\n"
            
            # Add key points if available
            if topic.get("key_points"):
                md += "### Puntos Clave\n"
                for point in topic["key_points"]:
                    md += f"- ✓ {point}\n"
                md += "\n"
            
            md += "---\n\n"
        
        # Add metadata footer
        md += f"""## 🏷️ Metadata
- **Archivo Original**: `{original_path.name}`
- **Procesado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Segmentos**: {len(topics)} temas principales
- **Palabras**: {metadata['word_count']:,}
"""
        
        return md
    
    def save_processed(self, content: str, original_filename: str) -> Path:
        """
        Save processed transcription to knowledge base.
        
        Args:
            content: Formatted markdown content
            original_filename: Name of original file
            
        Returns:
            Path to saved file
        """
        # Generate processed filename
        base_name = original_filename.replace("transcripcion_", "processed_")
        if not base_name.startswith("processed_"):
            base_name = f"processed_{base_name}"
        
        output_path = self.processed_dir / base_name
        
        # Save file
        output_path.write_text(content, encoding='utf-8')
        
        return output_path
    
    def process_transcription(self, file_path: Path) -> Tuple[Path, Dict[str, Any]]:
        """
        Process a single transcription file.
        
        Args:
            file_path: Path to transcription file
            
        Returns:
            Tuple of (processed_file_path, metadata)
        """
        print(f"[INFO] Procesando: {file_path.name}")
        
        # Extract metadata
        metadata = self.extract_metadata(file_path)
        print(f"   Fecha: {metadata['date']} | Palabras: {metadata['word_count']:,}")
        
        # Read content
        content = file_path.read_text(encoding='utf-8')
        
        # Detect topics
        print("   [INFO] Detectando temas...")
        topics = self.detect_topics(content)
        print(f"   [OK] Encontrados {len(topics)} temas")
        
        # Segment by topics
        topics = self.segment_by_topics(content, topics)
        
        # Format as professional markdown
        print("   [INFO] Generando markdown profesional...")
        formatted_md = self.format_professional_md(metadata, topics, file_path)
        
        # Save processed file
        output_path = self.save_processed(formatted_md, file_path.name)
        print(f"   [OK] Guardado en: {output_path}")
        
        return output_path, metadata
    
    def get_recent(self, n: int = 5) -> List[Path]:
        """
        Get N most recent transcriptions.
        
        Args:
            n: Number of recent files to return
            
        Returns:
            List of paths to recent transcriptions
        """
        files = self.load_from_directory()
        
        # Sort by modification time (most recent first)
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        return files[:n]
