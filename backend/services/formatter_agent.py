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
        
        # Minimax client
        api_key = os.getenv("MINIMAX_API_KEY")
        if api_key:
            self.client = OpenAI(
                base_url=os.getenv("MINIMAX_BASE_URL", "https://integrate.api.nvidia.com/v1"),
                api_key=api_key
            )
            self.model = os.getenv("MINIMAX_MODEL_NAME", "minimaxai/minimax-m2")
        else:
            self.client = None
            self.model = None
    
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
        
        if not self.client:
            yield FormatterProgress(
                job_id=job_id,
                current=0,
                total=len(job.files),
                file_name="",
                status="error",
                error="MINIMAX_API_KEY not configured"
            )
            return
        
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
        """Step: Format content using Minimax M2 with retry logic"""
        system_prompt = """Actúa como un redactor técnico y académico experto.

Genera un documento profesional en Markdown bien estructurado basado en la transcripción proporcionada.

El documento DEBE incluir:

1. **Resumen Ejecutivo**: Un párrafo conciso (3-5 líneas) que capture la esencia del contenido
2. **Puntos Clave**: Lista organizada de los conceptos más importantes discutidos
3. **Desarrollo Detallado**: Secciones temáticas con:
   - Encabezados claros y jerárquicos (##, ###)
   - Explicaciones elaboradas de cada tema
   - Ejemplos concretos cuando los haya
   - Conceptos técnicos bien explicados
4. **Conclusiones**: Síntesis de aprendizajes y próximos pasos si aplica

Formato requerido:
- Usa negritas para términos clave
- Usa listas para puntos importantes
- Usa bloques de código para términos técnicos o comandos
- Mantén el idioma original (Español)
- Organiza el contenido de forma lógica y pedagógica
- Elimina redundancias y muletillas del habla

NO incluyas timestamps ni marcadores de tiempo.
Genera un documento que sea útil para estudio y referencia académica."""

        user_content = f"""Fecha original: {file_data['metadata'].get('fecha', 'N/A')}
Temas: {file_data['metadata'].get('temas', 'Varios')}
Palabras originales: {file_data['metadata'].get('palabras', 'N/A')}

Contenido a formatear:

{file_data['clean_content'][:15000]}"""  # Limit to avoid token limits
        
        for attempt in range(max_retries + 1):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.5,
                    top_p=0.9,
                    max_tokens=8192
                )
                
                formatted_content = completion.choices[0].message.content.strip()
                
                # Add metadata header
                header = f"""---
original: {file_data['metadata'].get('original', file_data['file_name'])}
fecha: {file_data['metadata'].get('fecha', 'N/A')}
palabras_original: {file_data['metadata'].get('palabras', 'N/A')}
formateado_con: Minimax M2
fecha_formato: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
modelo: {self.model}
---

"""
                return header + formatted_content
                
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(2 * (2 ** attempt))  # Exponential backoff
                    continue
                raise
    
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
                
                return formatted_file
                
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(1 * (2 ** attempt))
                    continue
                raise
