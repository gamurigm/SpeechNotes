"""
Durable Formatter Agent
Handles formatting of transcriptions using Kimi K2-Thinking
Reads content from database and writes formatted content back to database (no file I/O).
"""

import os
import re
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv
from src.database.mongo_manager import MongoManager

load_dotenv()


class StepStatus(Enum):
    """Step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class FormatterProgress:
    """Progress update for formatting job"""
    job_id: str
    current: int
    total: int
    file_name: str
    status: str  # 'reading', 'formatting', 'saving', 'completed', 'error'
    output_path: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "current": self.current,
            "total": self.total,
            "file_name": self.file_name,
            "status": self.status,
            "output_path": self.output_path,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class FormatterJob:
    """Represents a formatting job"""
    job_id: str
    files: List[str]
    output_dir: str
    status: str = "pending"
    progress: List[FormatterProgress] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    successful: int = 0
    failed: int = 0


class FormatterAgent:
    """
    Durable agent for formatting transcriptions with Minimax M2
    Implements retry logic and progress streaming
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.jobs: Dict[str, FormatterJob] = {}
        
        # Initialize client with best available key (from ConfigService)
        from src.database.config_service import ConfigService
        _cfg = ConfigService()
        self.api_key = _cfg.get("NVIDIA_API_KEY_THINKING") or _cfg.get("MINIMAX_API_KEY")
        self.base_url = _cfg.get("NVIDIA_BASE_URL") or _cfg.get("MINIMAX_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.model = _cfg.get("FORMATTER_MODEL", "moonshotai/kimi-k2-thinking")
        
        if self.api_key:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        else:
            self.client = None
    
    def create_job(self, transcription_ids: List[str]) -> str:
        """Create a new formatting job with transcription IDs instead of file paths"""
        job_id = str(uuid.uuid4())
        job = FormatterJob(
            job_id=job_id,
            files=transcription_ids,
            output_dir=""
        )
        self.jobs[job_id] = job
        return job_id
    
    def get_job(self, job_id: str) -> Optional[FormatterJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    async def run_job(self, job_id: str) -> AsyncGenerator[FormatterProgress, None]:
        """
        Run formatting job reading from and writing to the database (no file I/O).
        Yields progress updates as they happen.
        """
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = "running"
        
        for idx, doc_id in enumerate(job.files, 1):
            try:
                # Step 1: Read from database
                yield FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=doc_id,
                    status="reading"
                )
                
                file_data = await self._read_db_step(doc_id)
                
                # Step 2: Format with AI
                yield FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_data["file_name"],
                    status="formatting"
                )
                
                formatted_content = await self._format_step(file_data)
                
                # Step 3: Save formatted content to database
                yield FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_data["file_name"],
                    status="saving"
                )
                
                await self._save_db_step(doc_id, formatted_content)
                
                # Success
                progress = FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_data["file_name"],
                    status="completed",
                    output_path=f"db://transcriptions/{doc_id}"
                )
                job.progress.append(progress)
                job.successful += 1
                yield progress
                
            except Exception as e:
                error_id = doc_id if 'doc_id' in locals() else f"index-{idx}"
                progress = FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=error_id,
                    status="error",
                    error=str(e)
                )
                job.progress.append(progress)
                job.failed += 1
                yield progress
        
        job.status = "completed"
        job.completed_at = datetime.now()
    
    async def _read_db_step(self, doc_id: str, max_retries: int = 2) -> Dict:
        """Step: Read transcription from database by document ID (no file I/O)."""
        loop = asyncio.get_running_loop()
        for attempt in range(max_retries + 1):
            try:
                db = await loop.run_in_executor(None, MongoManager)
                doc = await loop.run_in_executor(
                    None, lambda: db.transcriptions.find_one({"_id": doc_id})
                )
                
                if not doc:
                    raise FileNotFoundError(f"Transcription not found in database: {doc_id}")
                
                content = doc.get("raw_content") or doc.get("edited_content") or ""
                if not content:
                    raise ValueError(f"Transcription {doc_id} has no content")
                
                # Extract metadata from document fields
                metadata = {
                    "fecha": doc.get("date", "N/A"),
                    "palabras": str(doc.get("word_count", "N/A")),
                    "filename": doc.get("filename", ""),
                    "tipo": doc.get("source_type", "desconocido")
                }
                
                # Clean content (remove timestamp markers)
                clean_content = re.sub(r'\*\*\[\d{2}:\d{2}:\d{2}\]\*\*\s*', '', content)
                clean_content = re.sub(r'\*\*\d{2}:\d{2}:\d{2}\*\*\s*', '', clean_content)
                clean_content = re.sub(r'\[\d{2}:\d{2}:\d{2}\]\s*', '', clean_content)
                clean_content = re.sub(r'\n{3,}', '\n\n', clean_content).strip()
                
                return {
                    "doc_id": doc_id,
                    "file_name": doc.get("filename", f"doc_{doc_id}"),
                    "original_content": content,
                    "clean_content": clean_content,
                    "metadata": metadata,
                    "doc": doc
                }
                
            except Exception:
                if attempt < max_retries:
                    await asyncio.sleep(1 * (2 ** attempt))
                    continue
                raise
    
    async def _format_step(self, file_data: Dict, max_retries: int = 3) -> str:
        """Step: Format content using a Thinking Model for professional results"""
        system_prompt = """Eres un asistente de transcripción académica. Tu trabajo es tomar una transcripción de clase y producir un documento limpio, organizado y fácil de leer.

REGLAS ESTRICTAS:

1. **CORRECCIÓN**: Corrige errores de habla (muletillas, repeticiones, frases incompletas). No cambies el vocabulario ni el estilo del hablante.

2. **ORGANIZACIÓN**: Agrupa el contenido por tema usando encabezados `##`. Los encabezados deben reflejar exactamente los temas discutidos, no etiquetas genéricas.

3. **EXPANSIÓN DE DETALLE**: Si el hablante mencionó un concepto de forma breve o incompleta, explícalo con más claridad basándote SOLO en lo que dijo. No inventes información que no esté implícita en el texto.

4. **FIDELIDAD**: Conserva el orden y la esencia de lo que se dijo. No reorganices el contenido de forma que cambie el sentido.

5. **FORMATO**: Markdown limpio. Usa listas cuando el hablante enumere cosas. Resalta con **negrita** los términos técnicos o conceptos clave que el hablante mencionó explícitamente.

PROHIBIDO: No uses secciones de "Introducción", "Conclusiones" o "Glosario" a menos que el hablante haya tratado esos temas explícitamente.

IDIOMA: Español. Respeta el registro y tono del hablante."""

        user_content = f"""Metadata:
- Fecha: {file_data['metadata'].get('fecha', 'N/A')}
- Contexto: {file_data['metadata'].get('temas', 'Varios')}

Contenido base para procesar:
{file_data['clean_content'][:18000]}"""
        
        # Use the agent-configured model and key (from ConfigService, not os.getenv)
        thinking_model = self.model
        thinking_key = self.api_key

        if not thinking_key:
             return self._local_format(file_data) # Fallback

        client = OpenAI(
            base_url=self.base_url,
            api_key=thinking_key,
            timeout=180.0
        )

        loop = asyncio.get_running_loop()

        for attempt in range(max_retries + 1):
            try:
                print(f"[FORMATTER] Using Thinking Model ({thinking_model}) for {file_data['file_name']}...")
                completion = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=thinking_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=0.7,
                        top_p=0.9,
                        max_tokens=16384,
                        extra_body={
                            "min_thinking_tokens": 1024,
                            "max_thinking_tokens": 4096
                        } if "thinking" in thinking_model or "kimi" in thinking_model else {}
                    )
                )

                formatted_content = completion.choices[0].message.content.strip()

                # Remove thinking blocks if present
                formatted_content = re.sub(r'<thinking>.*?</thinking>', '', formatted_content, flags=re.DOTALL).strip()

                # Add metadata header
                header = f"""---
original: {file_data['metadata'].get('original', file_data['file_name'])}
fecha: {file_data['metadata'].get('fecha', 'N/A')}
formateado_con: Kimi K2-Thinking
fecha_formato: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
tipo: Profesional
---

"""
                return header + formatted_content

            except Exception:
                if attempt < max_retries:
                    await asyncio.sleep(2 * (2 ** attempt))  # Exponential backoff
                    continue
                raise

    def _local_format(self, file_data: Dict) -> str:
        """Simple local formatter (fallback when Minimax not configured).

        Produces an executive summary, key points, development sections
        and conclusions using basic heuristics.
        """
        text = file_data.get('clean_content', '')
        # Heuristics: split by headings or long pauses / double newlines
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

        # Executive summary: first 1-2 paragraphs
        summary = ''
        if paragraphs:
            summary = ' '.join(paragraphs[:2])
            if len(summary) > 500:
                summary = summary[:500].rsplit(' ', 1)[0] + '...'

        # Key points: extract short sentences with keywords or first lines
        key_points = []
        for p in paragraphs[:6]:
            # take first sentence-ish
            s = re.split(r'[\.\?!]\s+', p)[0]
            if len(s) > 10:
                key_points.append(s.strip())
        if not key_points and paragraphs:
            key_points = [paragraphs[0][:120]]

        # Development: group remaining paragraphs into sections of ~400-800 chars
        sections = []
        buffer = []
        buf_len = 0
        for p in paragraphs[2:]:
            buffer.append(p)
            buf_len += len(p)
            if buf_len > 800:
                sections.append('\n\n'.join(buffer))
                buffer = []
                buf_len = 0
        if buffer:
            sections.append('\n\n'.join(buffer))

        # Build markdown
        md = []
        md.append('## Resumen Ejecutivo')
        md.append(summary or 'No hay contenido suficiente para generar un resumen.')

        md.append('## Puntos Clave')
        for kp in key_points:
            md.append(f'- **{kp}**')

        md.append('## Desarrollo Detallado')
        for i, sec in enumerate(sections, 1):
            md.append(f'### Sección {i}')
            md.append(sec)

        md.append('## Conclusiones')
        md.append('Resumen de ideas clave y posibles próximos pasos.')

        return '\n\n'.join(md)
    
    async def _save_db_step(self, doc_id: str, formatted_content: str, max_retries: int = 2) -> None:
        """Step: Save formatted content to database (no file I/O)."""
        loop = asyncio.get_running_loop()
        for attempt in range(max_retries + 1):
            try:
                db = await loop.run_in_executor(None, MongoManager)

                result = await loop.run_in_executor(
                    None,
                    lambda db=db: db.transcriptions.update_one(
                        {"_id": doc_id},
                        {
                            "$set": {
                                "formatted_content": formatted_content,
                                "formatted_at": datetime.now(),
                                "is_formatted": True,
                                "formatter_model": self.model
                            }
                        }
                    )
                )
                
                if result.modified_count > 0:
                    print(f"[FORMATTER] Updated formatted_content for {doc_id}")
                else:
                    doc = await loop.run_in_executor(
                        None, lambda db=db: db.transcriptions.find_one({"_id": doc_id})
                    )
                    if doc:
                        print(f"[FORMATTER] Document {doc_id} found but content unchanged")
                    else:
                        formatted_doc = {
                            "_id": doc_id,
                            "filename": f"formatted_{doc_id}.md",
                            "formatted_content": formatted_content,
                            "formatted_at": datetime.now(),
                            "word_count": len(formatted_content.split()),
                            "processed": True,
                            "is_formatted": True
                        }
                        await loop.run_in_executor(
                            None, lambda db=db, formatted_doc=formatted_doc: db.transcriptions.insert_one(formatted_doc)
                        )
                        print(f"[FORMATTER] Created new formatted document: {doc_id}")
                
                return None
                
            except Exception:
                if attempt < max_retries:
                    await asyncio.sleep(1 * (2 ** attempt))
                    continue
                raise
