"""
Output Formatters - Strategy Pattern
Different strategies for formatting transcription output
"""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


class OutputFormatter(ABC):
    """
    Abstract formatter for transcription output
    Strategy Pattern: Different formatting strategies
    """
    
    @abstractmethod
    def format(self, transcript: str, metadata: dict) -> str:
        """Format transcript with metadata"""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this format"""
        pass


class MarkdownFormatter(OutputFormatter):
    """
    Markdown formatter for transcriptions
    SRP: Only responsible for Markdown formatting
    """
    
    def format(self, transcript: str, metadata: dict) -> str:
        """
        Format transcript as Markdown
        
        Args:
            transcript: Transcription text
            metadata: Dictionary with metadata (timestamp, duration, etc.)
            
        Returns:
            Formatted Markdown string
        """
        timestamp = metadata.get('timestamp', datetime.now())
        duration = metadata.get('duration_seconds', 0)
        duration_mins = int(duration // 60)
        duration_secs = int(duration % 60)
        
        title = metadata.get('title', 'Transcripción de Audio')
        audio_file = metadata.get('audio_file', 'N/A')
        language = metadata.get('language', 'es')
        word_count = len(transcript.split())
        char_count = len(transcript)
        
        now_str = datetime.now().strftime('%Y-%m-%d a las %H:%M:%S')
        md_content = f"""# {title}

## 📋 Metadata
- **Fecha:** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
- **Archivo:** `{audio_file}`
- **Idioma:** {language}
- **Duración:** {duration_mins}m {duration_secs}s
- **Palabras:** ~{word_count}
- **Caracteres:** {char_count}

---

## 📝 Transcripción

{transcript}

---

*Generado automáticamente el {now_str}*
"""
        
        return md_content
    
    def get_file_extension(self) -> str:
        return ".md"


class SegmentedMarkdownFormatter(OutputFormatter):
    """
    Markdown formatter with time-stamped segments
    SRP: Only responsible for segmented Markdown formatting
    """
    
    def format(self, segments: List[Tuple[datetime, str]], metadata: dict) -> str:
        """
        Format segmented transcript as Markdown
        
        Args:
            segments: List of (timestamp, text) tuples
            metadata: Dictionary with metadata
            
        Returns:
            Formatted Markdown string
        """
        if not segments:
            return ""
        
        start_time = segments[0][0]
        end_time = segments[-1][0]
        duration = (end_time - start_time).total_seconds()
        duration_mins = int(duration // 60)
        duration_secs = int(duration % 60)
        
        title = metadata.get('title', 'Transcripción en Tiempo Real')
        
        # Full text without timestamps
        full_text = " ".join([text for _, text in segments])
        
        md_content = f"""# {title}

## 📋 Metadata
- **Fecha:** {start_time.strftime("%Y-%m-%d %H:%M:%S")}
- **Duración:** {duration_mins}m {duration_secs}s
- **Segmentos:** {len(segments)}
- **Método:** {metadata.get('method', 'Segmentación automática')}

---

## 📝 Transcripción Completa

{full_text}

---

## 🕐 Transcripción por Segmentos

"""
        
        for timestamp, text in segments:
            time_str = timestamp.strftime("%H:%M:%S")
            md_content += f"**[{time_str}]** {text}\n\n"
        
        now_str = datetime.now().strftime('%Y-%m-%d a las %H:%M:%S')
        md_content += f"""---

*Generado automáticamente el {now_str}*
"""
        
        return md_content
    
    def get_file_extension(self) -> str:
        return ".md"


class PlainTextFormatter(OutputFormatter):
    """
    Plain text formatter
    SRP: Only responsible for plain text formatting
    """
    
    def format(self, transcript: str, metadata: dict) -> str:
        """Format as plain text"""
        timestamp = metadata.get('timestamp', datetime.now())
        return f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}]\n\n{transcript}\n"
    
    def get_file_extension(self) -> str:
        return ".txt"


class OutputWriter:
    """
    Writes formatted output to files
    SRP: Only responsible for file I/O
    """
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize output writer
        
        Args:
            output_dir: Directory for output files, defaults to 'notas/'
        """
        self.output_dir = output_dir or Path("notas")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write(
        self, 
        content: str, 
        filename: str = None, 
        extension: str = ".md"
    ) -> Path:
        """
        Write content to file
        
        Args:
            content: Content to write
            filename: Optional filename, auto-generated if None
            extension: File extension
            
        Returns:
            Path to written file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcripcion_{timestamp}{extension}"
        
        if not filename.endswith(extension):
            filename += extension
        
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        
        return file_path


class FormatterFactory:
    """
    Factory for creating formatters
    Factory Pattern: Centralized formatter creation
    """
    
    _formatters = {
        'markdown': MarkdownFormatter,
        'segmented_markdown': SegmentedMarkdownFormatter,
        'plain': PlainTextFormatter,
    }
    
    @classmethod
    def create(cls, format_type: str = 'markdown') -> OutputFormatter:
        """
        Create a formatter instance
        
        Args:
            format_type: Type of formatter ('markdown', 'segmented_markdown', 'plain')
            
        Returns:
            Formatter instance
            
        Raises:
            ValueError: If format_type is unknown
        """
        formatter_class = cls._formatters.get(format_type)
        if not formatter_class:
            raise ValueError(f"Unknown format type: {format_type}")
        return formatter_class()
