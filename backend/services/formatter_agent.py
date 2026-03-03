"""
Durable Formatter Agent
Handles formatting of markdown transcriptions using Minimax M2
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
    
    def create_job(self, files: List[str], output_dir: str = "notas") -> str:
        """Create a new formatting job"""
        job_id = str(uuid.uuid4())
        job = FormatterJob(
            job_id=job_id,
            files=files,
            output_dir=output_dir
        )
        self.jobs[job_id] = job
        return job_id
    
    def get_job(self, job_id: str) -> Optional[FormatterJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    async def run_job(self, job_id: str) -> AsyncGenerator[FormatterProgress, None]:
        """
        Run formatting job with progress updates
        Yields progress updates as they happen
        """
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = "running"
        
        for idx, file_path in enumerate(job.files, 1):
            file_name = Path(file_path).name
            
            try:
                # Step 1: Read file
                yield FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_name,
                    status="reading"
                )
                
                file_data = await self._read_file_step(file_path)
                
                # Step 2: Format with Minimax
                yield FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_name,
                    status="formatting"
                )
                
                formatted_content = await self._format_step(file_data)
                
                # Step 3: Save formatted file
                yield FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_name,
                    status="saving"
                )
                
                output_path = await self._save_file_step(file_data, formatted_content, job.output_dir)
                
                # Success
                progress = FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_name,
                    status="completed",
                    output_path=str(output_path)
                )
                job.progress.append(progress)
                job.successful += 1
                yield progress
                
            except Exception as e:
                # Error
                progress = FormatterProgress(
                    job_id=job_id,
                    current=idx,
                    total=len(job.files),
                    file_name=file_name,
                    status="error",
                    error=str(e)
                )
                job.progress.append(progress)
                job.failed += 1
                yield progress
        
        job.status = "completed"
        job.completed_at = datetime.now()
    
    async def _read_file_step(self, file_path: str, max_retries: int = 2) -> Dict:
        """Step: Read and parse markdown file with retry logic"""
        for attempt in range(max_retries + 1):
            try:
                full_path = self.project_root / file_path

                if not full_path.exists():
                    # Try common fallback: maybe the original was backed up as .md.original
                    try:
                        backup_path = full_path.with_suffix(full_path.suffix + '.original')
                        if backup_path.exists():
                            print(f"[FORMATTER] Original file missing, using backup: {backup_path}")
                            full_path = backup_path
                        else:
                            # Also try removing any leading 'notas/' if double-prefixed
                            alt = self.project_root / Path(file_path).name
                            if alt.exists():
                                print(f"[FORMATTER] Using alternate path without folder: {alt}")
                                full_path = alt
                            else:
                                raise FileNotFoundError(f"File not found: {file_path}")
                    except Exception:
                        raise FileNotFoundError(f"File not found: {file_path}")
                
                content = full_path.read_text(encoding='utf-8')
                
                # Extract YAML frontmatter metadata
                metadata = {}
                yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if yaml_match:
                    yaml_content = yaml_match[1]
                    for line in yaml_content.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
                
                # Extract clean text (remove timestamps, metadata sections)
                clean_content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
                clean_content = re.sub(r'## 📋 (Metadata|Tabla de Contenidos).*?---', '', clean_content, flags=re.DOTALL)
                clean_content = re.sub(r'\*\*\[\d{2}:\d{2}:\d{2}\]\*\*\s*', '', clean_content)
                clean_content = re.sub(r'\n{3,}', '\n\n', clean_content).strip()
                
                return {
                    "file_path": str(full_path),
                    "file_name": full_path.name,
                    "original_content": content,
                    "clean_content": clean_content,
                    "metadata": metadata
                }
                
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(1 * (2 ** attempt))  # Exponential backoff
                    continue
                raise
    
    async def _format_step(self, file_data: Dict, max_retries: int = 3) -> str:
        """Step: Format content using a Thinking Model for professional results"""
        system_prompt = """Actúa como un asistente de IA de élite especializado en redacción académica y síntesis de alto nivel. 
Tu tarea es tomar una transcripción bruta y REESCRIBIRLA COMPLETAMENTE como un documento profesional.

ESTRUCURA OBLIGATORIA:

# Título del Documento (Sin etiquetas, claro y profesional)

## 🎯 Introducción y Contexto
Un resumen ejecutivo de alto nivel que sitúe al lector en el tema tratado (mínimo 6 líneas).

## 🧩 Ejes Temáticos Principales
Identifica y desarrolla los temas clave del contenido. NO uses la estructura de la transcripción original.
- Cada tema debe tener su propio encabezado (## o ###).
- Sintetiza la información de forma coherente, eliminando repeticiones.
- Usa **negritas** para términos técnicos.

## 📝 Glosario de Conceptos Clave
Una sección dedicada a definir los términos más importantes mencionados durante la sesión.

## 🏁 Síntesis y Conclusiones
Un cierre profesional que resuma los aprendizajes y mencione próximos pasos o áreas de estudio relacionadas.

REGLAS CRÍTICAS DE FORMATO:
1. **PROHIBIDO**: No incluyas marcas de tiempo (00:00:00).
2. **PROHIBIDO**: No menciones "Tema 1", "Segmento X" o etiquetas similares de la transcripción original.
3. **SÍNTESIS TOTAL**: Tu objetivo no es "limpiar" el texto, sino **RAZONAR** sobre él y generar un documento nuevo y estructurado.
4. **LIMPIEZA**: Elimina cualquier muletilla, duda o error de habla presente en el audio original.
5. **MARKDOWN**: Usa Markdown fluido y profesional.
6. **IDIOMA**: Español."""

        user_content = f"""Metadata:
- Fecha: {file_data['metadata'].get('fecha', 'N/A')}
- Contexto: {file_data['metadata'].get('temas', 'Varios')}

Contenido base para procesar:
{file_data['clean_content'][:18000]}"""
        
        # Use a thinking model if configured
        thinking_model = os.getenv("FORMATTER_MODEL", "moonshotai/kimi-k2-thinking")
        thinking_key = os.getenv("NVIDIA_API_KEY_THINKING") or os.getenv("MINIMAX_API_KEY")

        if not thinking_key:
             return self._local_format(file_data) # Fallback

        client = OpenAI(
            base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            api_key=thinking_key
        )

        for attempt in range(max_retries + 1):
            try:
                print(f"[FORMATTER] Using Thinking Model ({thinking_model}) for {file_data['file_name']}...")
                completion = client.chat.completions.create(
                    model=thinking_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7, # Balanced for creativity and structure
                    top_p=0.9,
                    max_tokens=16384,
                    extra_body={
                        "min_thinking_tokens": 1024,
                        "max_thinking_tokens": 4096
                    } if "thinking" in thinking_model or "kimi" in thinking_model else {}
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

            except Exception as e:
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
    
    async def _save_file_step(self, file_data: Dict, formatted_content: str, output_dir: str, max_retries: int = 2) -> Path:
        """Step: Save formatted file and backup original with retry logic"""
        for attempt in range(max_retries + 1):
            try:
                original_path = Path(file_data["file_path"])
                output_path = self.project_root / output_dir
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Backup original if not already backed up
                backup_path = original_path.with_suffix('.md.original')
                if not backup_path.exists():
                    original_path.rename(backup_path)
                
                # Save formatted version
                formatted_file = output_path / f"{original_path.stem}_formatted.md"
                formatted_file.write_text(formatted_content, encoding='utf-8')

                # Ingest formatted content into original MongoDB document
                try:
                    db = MongoManager()
                    # Find the original document
                    # The original filename is in file_data["file_name"] (e.g., "clase1.md")
                    original_filename = file_data["file_name"]
                    
                    # Also try without extension just in case
                    filename_stem = Path(original_filename).stem
                    
                    doc = db.transcriptions.find_one({
                        "$or": [
                            {"filename": original_filename},
                            {"filename": {"$regex": f"^{filename_stem}", "$options": "i"}}
                        ]
                    })
                    
                    if doc:
                        # Update existing document
                        db.transcriptions.update_one(
                            {"_id": doc["_id"]},
                            {
                                "$set": {
                                    "formatted_content": formatted_content,
                                    "formatted_at": datetime.now(),
                                    "is_formatted": True,
                                    "formatter_model": self.model
                                }
                            }
                        )
                        print(f"[FORMATTER] Updated original document in MongoDB: {original_filename}")
                    else:
                        # If not found, create a new one (as fallback)
                        formatted_doc = {
                            "filename": formatted_file.name,
                            "original_filename": original_filename,
                            "formatted_content": formatted_content,
                            "formatted_at": datetime.now(),
                            "word_count": len(formatted_content.split()),
                            "source_path": str(formatted_file),
                            "processed": True,
                            "is_formatted": True
                        }
                        db.transcriptions.insert_one(formatted_doc)
                        print(f"[FORMATTER] Original not found. Inserted new formatted document: {formatted_file.name}")
                except Exception as e:
                    print(f"[FORMATTER] Warning: failed to ingest formatted file into MongoDB: {e}")

                return formatted_file
                
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(1 * (2 ** attempt))
                    continue
                raise
