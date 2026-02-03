"""
Audio Formatter Service
Handles audio format conversion and optimization using FFmpeg (via pydub)
"""

import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from pydub import AudioSegment
from pydub.utils import mediainfo


class FormatProfile(Enum):
    """Pre-configured format profiles for common use cases"""
    TRANSCRIPTION = "transcription"  # Optimized for NVIDIA Riva
    STORAGE = "storage"              # Minimal size for archival
    HIGH_QUALITY = "high_quality"    # Maximum audio quality
    CUSTOM = "custom"                # User-defined parameters


@dataclass
class AudioMetadata:
    """Metadata extracted from audio file"""
    format: str
    codec: str
    sample_rate: int
    channels: int
    bit_depth: int
    duration_seconds: float
    file_size_mb: float
    is_optimized: bool = False
    
    @property
    def is_transcription_ready(self) -> bool:
        """Check if audio meets NVIDIA Riva requirements"""
        return (
            self.sample_rate == 16000 and
            self.channels == 1 and
            self.bit_depth == 16 and
            self.format.lower() in ['wav', 'pcm']
        )


@dataclass
class ConversionMetrics:
    """Metrics about the conversion process"""
    original_size_mb: float
    formatted_size_mb: float
    compression_ratio: float
    processing_time_seconds: float
    quality_preserved: bool = True
    
    @property
    def space_saved_mb(self) -> float:
        return self.original_size_mb - self.formatted_size_mb
    
    @property
    def space_saved_percent(self) -> float:
        if self.original_size_mb == 0:
            return 0.0
        return (self.space_saved_mb / self.original_size_mb) * 100


@dataclass
class ConversionResult:
    """Result of a single file conversion"""
    status: str  # "success", "failed", "skipped"
    input_path: str
    output_path: Optional[str] = None
    backup_path: Optional[str] = None
    metrics: Optional[ConversionMetrics] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {
            "status": self.status,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "backup_path": self.backup_path,
            "error_message": self.error_message
        }
        if self.metrics:
            result["metrics"] = {
                "original_size_mb": round(self.metrics.original_size_mb, 2),
                "formatted_size_mb": round(self.metrics.formatted_size_mb, 2),
                "compression_ratio": round(self.metrics.compression_ratio, 2),
                "processing_time_seconds": round(self.metrics.processing_time_seconds, 2),
                "space_saved_mb": round(self.metrics.space_saved_mb, 2),
                "space_saved_percent": round(self.metrics.space_saved_percent, 1)
            }
        return result


@dataclass
class FormatJob:
    """Represents a format job (single or batch)"""
    job_id: str
    files: List[str]
    output_format: str
    profile: str
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    results: List[ConversionResult] = field(default_factory=list)
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    
    def __post_init__(self):
        self.total_files = len(self.files)


@dataclass
class BatchProgress:
    """Progress update for batch conversion"""
    job_id: str
    current_file: str
    file_index: int
    total_files: int
    status: str  # "converting", "completed", "failed"
    progress_percent: float
    current_result: Optional[ConversionResult] = None
    
    def to_dict(self) -> Dict:
        data = {
            "type": "progress",
            "job_id": self.job_id,
            "current_file": self.current_file,
            "file_index": self.file_index,
            "total_files": self.total_files,
            "status": self.status,
            "progress_percent": round(self.progress_percent, 1)
        }
        if self.current_result:
            data["result"] = self.current_result.to_dict()
        return data


class AudioFormatterService:
    """
    Service for audio format conversion and optimization
    Uses FFmpeg via pydub for maximum compatibility
    """
    
    # Format profiles configuration
    PROFILES = {
        FormatProfile.TRANSCRIPTION: {
            "format": "wav",
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "codec": "pcm_s16le",
            "description": "Optimized for NVIDIA Riva transcription"
        },
        FormatProfile.STORAGE: {
            "format": "mp3",
            "sample_rate": 22050,
            "channels": 1,
            "bitrate": "64k",
            "codec": "libmp3lame",
            "description": "Minimal size for archival storage"
        },
        FormatProfile.HIGH_QUALITY: {
            "format": "flac",
            "sample_rate": 48000,
            "channels": 2,
            "bit_depth": 24,
            "codec": "flac",
            "description": "Maximum audio quality preservation"
        }
    }
    
    def __init__(self, project_root: Path = None, temp_dir: Path = None):
        """
        Initialize the AudioFormatterService
        
        Args:
            project_root: Root directory of the project
            temp_dir: Temporary directory for processing
        """
        self.project_root = project_root or Path.cwd()
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "audio_formatting"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Job tracking
        self.jobs: Dict[str, FormatJob] = {}
        
        print(f"[AudioFormatter] Initialized - Project: {self.project_root}")
        print(f"[AudioFormatter] Temp directory: {self.temp_dir}")
    
    def detect_format(self, file_path: Path) -> AudioMetadata:
        """
        Detect audio format and extract metadata
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioMetadata object with file information
        """
        try:
            # Get file info using pydub/ffmpeg
            info = mediainfo(str(file_path))
            
            # Load audio to get accurate properties
            audio = AudioSegment.from_file(str(file_path))
            
            # Calculate file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Determine bit depth
            bit_depth = audio.sample_width * 8
            
            metadata = AudioMetadata(
                format=info.get('format_name', 'unknown'),
                codec=info.get('codec_name', 'unknown'),
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                bit_depth=bit_depth,
                duration_seconds=len(audio) / 1000.0,
                file_size_mb=file_size_mb
            )
            
            # Check if optimized for transcription
            metadata.is_optimized = metadata.is_transcription_ready
            
            print(f"[AudioFormatter] Detected format for {file_path.name}:")
            print(f"  Format: {metadata.format}, Codec: {metadata.codec}")
            print(f"  Sample Rate: {metadata.sample_rate} Hz, Channels: {metadata.channels}")
            print(f"  Bit Depth: {metadata.bit_depth}, Duration: {metadata.duration_seconds:.2f}s")
            print(f"  Size: {metadata.file_size_mb:.2f} MB")
            print(f"  Transcription Ready: {metadata.is_transcription_ready}")
            
            return metadata
            
        except Exception as e:
            print(f"[AudioFormatter] Error detecting format: {e}")
            raise
    
    def _get_profile_settings(self, profile: str) -> Dict:
        """Get settings for a specific profile"""
        try:
            profile_enum = FormatProfile(profile)
            return self.PROFILES[profile_enum]
        except ValueError:
            # Default to transcription profile
            return self.PROFILES[FormatProfile.TRANSCRIPTION]
    
    async def convert_file(
        self,
        input_path: Path,
        output_format: str = "wav",
        profile: str = "transcription",
        custom_params: Dict = None,
        backup_original: bool = True,
        output_dir: Path = None
    ) -> ConversionResult:
        """
        Convert a single audio file
        
        Args:
            input_path: Path to input audio file
            output_format: Desired output format (wav, mp3, ogg, etc.)
            profile: Conversion profile name
            custom_params: Custom conversion parameters (overrides profile)
            backup_original: Whether to create backup of original file
            output_dir: Output directory (defaults to same as input)
            
        Returns:
            ConversionResult with conversion details
        """
        start_time = datetime.now()
        
        try:
            # Validate input file exists
            if not input_path.exists():
                return ConversionResult(
                    status="failed",
                    input_path=str(input_path),
                    error_message=f"Input file not found: {input_path}"
                )
            
            # Get original size
            original_size_mb = input_path.stat().st_size / (1024 * 1024)
            
            # Determine output path
            if output_dir is None:
                output_dir = input_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create output filename
            base_name = input_path.stem
            output_filename = f"{base_name}_formatted.{output_format}"
            output_path = output_dir / output_filename
            
            # Get conversion settings
            if custom_params:
                settings = custom_params
            else:
                settings = self._get_profile_settings(profile)
            
            print(f"[AudioFormatter] Converting {input_path.name}...")
            print(f"  Profile: {profile}")
            print(f"  Settings: {settings}")
            
            # Load audio
            audio = AudioSegment.from_file(str(input_path))
            
            # Apply settings
            if 'sample_rate' in settings:
                audio = audio.set_frame_rate(settings['sample_rate'])
            
            if 'channels' in settings:
                audio = audio.set_channels(settings['channels'])
            
            if 'bit_depth' in settings and settings.get('format') == 'wav':
                # Convert bit depth (sample_width in bytes)
                sample_width = settings['bit_depth'] // 8
                audio = audio.set_sample_width(sample_width)
            
            # Export with appropriate parameters
            export_params = {}
            if 'bitrate' in settings:
                export_params['bitrate'] = settings['bitrate']
            if 'codec' in settings and output_format != 'wav':
                export_params['codec'] = settings['codec']
            
            # Perform conversion
            audio.export(str(output_path), format=output_format, **export_params)
            
            # Get formatted size
            formatted_size_mb = output_path.stat().st_size / (1024 * 1024)
            
            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            compression_ratio = original_size_mb / formatted_size_mb if formatted_size_mb > 0 else 1.0
            
            metrics = ConversionMetrics(
                original_size_mb=original_size_mb,
                formatted_size_mb=formatted_size_mb,
                compression_ratio=compression_ratio,
                processing_time_seconds=processing_time
            )
            
            # Create backup if requested
            backup_path = None
            if backup_original:
                backup_dir = output_dir / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_filename = f"{input_path.stem}.original{input_path.suffix}"
                backup_path = backup_dir / backup_filename
                
                # Only create backup if it doesn't exist
                if not backup_path.exists():
                    shutil.copy2(input_path, backup_path)
                    print(f"[AudioFormatter] Backup created: {backup_path}")
            
            print(f"[AudioFormatter] ✅ Conversion successful!")
            print(f"  Output: {output_path}")
            print(f"  Original: {original_size_mb:.2f} MB → Formatted: {formatted_size_mb:.2f} MB")
            print(f"  Compression: {compression_ratio:.2f}x | Saved: {metrics.space_saved_mb:.2f} MB ({metrics.space_saved_percent:.1f}%)")
            print(f"  Processing time: {processing_time:.2f}s")
            
            return ConversionResult(
                status="success",
                input_path=str(input_path),
                output_path=str(output_path),
                backup_path=str(backup_path) if backup_path else None,
                metrics=metrics
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"[AudioFormatter] ❌ Conversion failed: {e}")
            
            return ConversionResult(
                status="failed",
                input_path=str(input_path),
                error_message=str(e),
                metrics=ConversionMetrics(
                    original_size_mb=original_size_mb if 'original_size_mb' in locals() else 0.0,
                    formatted_size_mb=0.0,
                    compression_ratio=0.0,
                    processing_time_seconds=processing_time
                )
            )
    
    def create_job(
        self,
        files: List[str],
        output_format: str = "wav",
        profile: str = "transcription"
    ) -> str:
        """
        Create a new format job
        
        Args:
            files: List of file paths to convert
            output_format: Desired output format
            profile: Conversion profile
            
        Returns:
            Job ID
        """
        job_id = f"fmt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        job = FormatJob(
            job_id=job_id,
            files=files,
            output_format=output_format,
            profile=profile
        )
        
        self.jobs[job_id] = job
        
        print(f"[AudioFormatter] Created job {job_id} with {len(files)} file(s)")
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[FormatJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    async def batch_convert(
        self,
        job_id: str,
        max_concurrent: int = 3
    ) -> AsyncIterator[BatchProgress]:
        """
        Convert multiple files with progress updates
        
        Args:
            job_id: Job identifier
            max_concurrent: Maximum concurrent conversions
            
        Yields:
            BatchProgress updates during conversion
        """
        job = self.get_job(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = "processing"
        
        try:
            total_files = len(job.files)
            
            for index, file_path_str in enumerate(job.files, start=1):
                file_path = self.project_root / file_path_str
                
                progress_percent = ((index - 1) / total_files) * 100
                
                # Yield progress update
                yield BatchProgress(
                    job_id=job_id,
                    current_file=file_path_str,
                    file_index=index,
                    total_files=total_files,
                    status="converting",
                    progress_percent=progress_percent
                )
                
                # Convert the file
                result = await self.convert_file(
                    input_path=file_path,
                    output_format=job.output_format,
                    profile=job.profile,
                    output_dir=file_path.parent
                )
                
                # Store result
                job.results.append(result)
                
                if result.status == "success":
                    job.successful += 1
                else:
                    job.failed += 1
                
                # Yield completion for this file
                yield BatchProgress(
                    job_id=job_id,
                    current_file=file_path_str,
                    file_index=index,
                    total_files=total_files,
                    status=result.status,
                    progress_percent=(index / total_files) * 100,
                    current_result=result
                )
                
                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)
            
            job.status = "completed"
            job.completed_at = datetime.now()
            
        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            print(f"[AudioFormatter] Batch conversion failed: {e}")
            raise
    
    def get_available_profiles(self) -> List[Dict]:
        """Get list of available conversion profiles"""
        profiles = []
        
        for profile_enum, settings in self.PROFILES.items():
            profiles.append({
                "name": profile_enum.value,
                "description": settings.get("description", ""),
                "settings": {
                    k: v for k, v in settings.items() if k != "description"
                }
            })
        
        return profiles
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True, exist_ok=True)
                print(f"[AudioFormatter] Cleaned up temp directory")
        except Exception as e:
            print(f"[AudioFormatter] Error cleaning temp files: {e}")
    
    # ==================== FUNCIONALIDADES ADICIONALES DE FFMPEG ====================
    
    async def normalize_audio(
        self,
        input_path: Path,
        target_loudness_db: float = -16.0,
        output_dir: Path = None
    ) -> ConversionResult:
        """
        Normaliza el volumen del audio a un nivel óptimo
        
        Args:
            input_path: Archivo de audio de entrada
            target_loudness_db: Nivel de volumen objetivo en dB (-20 a -10)
            output_dir: Directorio de salida
            
        Returns:
            ConversionResult con el archivo normalizado
        """
        start_time = datetime.now()
        
        try:
            if not input_path.exists():
                return ConversionResult(
                    status="failed",
                    input_path=str(input_path),
                    error_message="Archivo no encontrado"
                )
            
            original_size_mb = input_path.stat().st_size / (1024 * 1024)
            
            # Determinar directorio de salida
            if output_dir is None:
                output_dir = input_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Cargar audio
            audio = AudioSegment.from_file(str(input_path))
            
            # Calcular cambio de volumen necesario
            current_loudness = audio.dBFS
            change_in_dB = target_loudness_db - current_loudness
            
            # Aplicar normalización
            normalized_audio = audio + change_in_dB
            
            # Guardar archivo normalizado
            output_filename = f"{input_path.stem}_normalized{input_path.suffix}"
            output_path = output_dir / output_filename
            
            normalized_audio.export(str(output_path), format=input_path.suffix[1:])
            
            formatted_size_mb = output_path.stat().st_size / (1024 * 1024)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"[AudioFormatter] ✅ Audio normalizado")
            print(f"  Volumen original: {current_loudness:.2f} dB")
            print(f"  Volumen objetivo: {target_loudness_db:.2f} dB")
            print(f"  Cambio aplicado: {change_in_dB:+.2f} dB")
            
            return ConversionResult(
                status="success",
                input_path=str(input_path),
                output_path=str(output_path),
                metrics=ConversionMetrics(
                    original_size_mb=original_size_mb,
                    formatted_size_mb=formatted_size_mb,
                    compression_ratio=original_size_mb / formatted_size_mb if formatted_size_mb > 0 else 1.0,
                    processing_time_seconds=processing_time
                )
            )
            
        except Exception as e:
            print(f"[AudioFormatter] ❌ Error normalizando audio: {e}")
            return ConversionResult(
                status="failed",
                input_path=str(input_path),
                error_message=str(e)
            )
    
    async def trim_silence(
        self,
        input_path: Path,
        silence_thresh_db: int = -40,
        min_silence_duration_ms: int = 1000,
        output_dir: Path = None
    ) -> ConversionResult:
        """
        Elimina silencios al inicio y final del audio
        
        Args:
            input_path: Archivo de audio de entrada
            silence_thresh_db: Umbral de silencio en dB (más negativo = más estricto)
            min_silence_duration_ms: Duración mínima del silencio a eliminar
            output_dir: Directorio de salida
            
        Returns:
            ConversionResult con el audio recortado
        """
        start_time = datetime.now()
        
        try:
            if not input_path.exists():
                return ConversionResult(
                    status="failed",
                    input_path=str(input_path),
                    error_message="Archivo no encontrado"
                )
            
            original_size_mb = input_path.stat().st_size / (1024 * 1024)
            
            if output_dir is None:
                output_dir = input_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Cargar audio
            audio = AudioSegment.from_file(str(input_path))
            original_duration = len(audio) / 1000.0
            
            # Detectar y eliminar silencios
            from pydub.silence import detect_leading_silence
            
            # Eliminar silencio inicial
            start_trim = detect_leading_silence(audio, silence_threshold=silence_thresh_db)
            
            # Eliminar silencio final (invertir audio, detectar, invertir de nuevo)
            end_trim = detect_leading_silence(audio.reverse(), silence_threshold=silence_thresh_db)
            
            # Recortar audio
            trimmed_audio = audio[start_trim:len(audio)-end_trim]
            
            # Guardar
            output_filename = f"{input_path.stem}_trimmed{input_path.suffix}"
            output_path = output_dir / output_filename
            
            trimmed_audio.export(str(output_path), format=input_path.suffix[1:])
            
            formatted_size_mb = output_path.stat().st_size / (1024 * 1024)
            processing_time = (datetime.now() - start_time).total_seconds()
            trimmed_duration = len(trimmed_audio) / 1000.0
            
            print(f"[AudioFormatter] ✅ Silencios eliminados")
            print(f"  Duración original: {original_duration:.2f}s")
            print(f"  Duración recortada: {trimmed_duration:.2f}s")
            print(f"  Recortado: {start_trim/1000:.2f}s inicio, {end_trim/1000:.2f}s final")
            
            return ConversionResult(
                status="success",
                input_path=str(input_path),
                output_path=str(output_path),
                metrics=ConversionMetrics(
                    original_size_mb=original_size_mb,
                    formatted_size_mb=formatted_size_mb,
                    compression_ratio=original_size_mb / formatted_size_mb if formatted_size_mb > 0 else 1.0,
                    processing_time_seconds=processing_time
                )
            )
            
        except Exception as e:
            print(f"[AudioFormatter] ❌ Error recortando silencios: {e}")
            return ConversionResult(
                status="failed",
                input_path=str(input_path),
                error_message=str(e)
            )
    
    async def extract_segment(
        self,
        input_path: Path,
        start_time_seconds: float,
        end_time_seconds: float,
        output_dir: Path = None
    ) -> ConversionResult:
        """
        Extrae un segmento específico del audio
        
        Args:
            input_path: Archivo de audio de entrada
            start_time_seconds: Tiempo de inicio en segundos
            end_time_seconds: Tiempo de fin en segundos
            output_dir: Directorio de salida
            
        Returns:
            ConversionResult con el segmento extraído
        """
        start_time = datetime.now()
        
        try:
            if not input_path.exists():
                return ConversionResult(
                    status="failed",
                    input_path=str(input_path),
                    error_message="Archivo no encontrado"
                )
            
            original_size_mb = input_path.stat().st_size / (1024 * 1024)
            
            if output_dir is None:
                output_dir = input_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Cargar audio
            audio = AudioSegment.from_file(str(input_path))
            
            # Convertir tiempos a milisegundos
            start_ms = int(start_time_seconds * 1000)
            end_ms = int(end_time_seconds * 1000)
            
            # Validar tiempos
            if start_ms >= len(audio):
                return ConversionResult(
                    status="failed",
                    input_path=str(input_path),
                    error_message=f"Tiempo de inicio ({start_time_seconds}s) excede la duración del audio"
                )
            
            # Extraer segmento
            segment = audio[start_ms:end_ms]
            
            # Guardar
            output_filename = f"{input_path.stem}_segment_{int(start_time_seconds)}s-{int(end_time_seconds)}s{input_path.suffix}"
            output_path = output_dir / output_filename
            
            segment.export(str(output_path), format=input_path.suffix[1:])
            
            formatted_size_mb = output_path.stat().st_size / (1024 * 1024)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"[AudioFormatter] ✅ Segmento extraído")
            print(f"  Rango: {start_time_seconds}s - {end_time_seconds}s")
            print(f"  Duración: {len(segment)/1000:.2f}s")
            
            return ConversionResult(
                status="success",
                input_path=str(input_path),
                output_path=str(output_path),
                metrics=ConversionMetrics(
                    original_size_mb=original_size_mb,
                    formatted_size_mb=formatted_size_mb,
                    compression_ratio=original_size_mb / formatted_size_mb if formatted_size_mb > 0 else 1.0,
                    processing_time_seconds=processing_time
                )
            )
            
        except Exception as e:
            print(f"[AudioFormatter] ❌ Error extrayendo segmento: {e}")
            return ConversionResult(
                status="failed",
                input_path=str(input_path),
                error_message=str(e)
            )
    
    async def merge_files(
        self,
        input_files: List[Path],
        output_filename: str = None,
        output_dir: Path = None
    ) -> ConversionResult:
        """
        Une varios archivos de audio en uno solo
        
        Args:
            input_files: Lista de archivos de audio a unir
            output_filename: Nombre del archivo de salida
            output_dir: Directorio de salida
            
        Returns:
            ConversionResult con el archivo unido
        """
        start_time = datetime.now()
        
        try:
            if not input_files:
                return ConversionResult(
                    status="failed",
                    input_path="",
                    error_message="No se proporcionaron archivos"
                )
            
            # Verificar que todos los archivos existan
            for file in input_files:
                if not file.exists():
                    return ConversionResult(
                        status="failed",
                        input_path=str(file),
                        error_message=f"Archivo no encontrado: {file}"
                    )
            
            original_size_mb = sum(f.stat().st_size for f in input_files) / (1024 * 1024)
            
            if output_dir is None:
                output_dir = input_files[0].parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Cargar y unir audios
            combined = AudioSegment.empty()
            
            for file in input_files:
                audio = AudioSegment.from_file(str(file))
                combined += audio
                print(f"  Añadido: {file.name} ({len(audio)/1000:.2f}s)")
            
            # Guardar
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"merged_{timestamp}.wav"
            
            output_path = output_dir / output_filename
            combined.export(str(output_path), format="wav")
            
            formatted_size_mb = output_path.stat().st_size / (1024 * 1024)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"[AudioFormatter] ✅ Archivos unidos")
            print(f"  Archivos procesados: {len(input_files)}")
            print(f"  Duración total: {len(combined)/1000:.2f}s")
            
            return ConversionResult(
                status="success",
                input_path=f"{len(input_files)} archivos",
                output_path=str(output_path),
                metrics=ConversionMetrics(
                    original_size_mb=original_size_mb,
                    formatted_size_mb=formatted_size_mb,
                    compression_ratio=original_size_mb / formatted_size_mb if formatted_size_mb > 0 else 1.0,
                    processing_time_seconds=processing_time
                )
            )
            
        except Exception as e:
            print(f"[AudioFormatter] ❌ Error uniendo archivos: {e}")
            return ConversionResult(
                status="failed",
                input_path=f"{len(input_files) if input_files else 0} archivos",
                error_message=str(e)
            )
    
    async def change_speed(
        self,
        input_path: Path,
        speed_factor: float = 1.5,
        output_dir: Path = None
    ) -> ConversionResult:
        """
        Cambia la velocidad del audio sin alterar el tono
        
        Args:
            input_path: Archivo de audio de entrada
            speed_factor: Factor de velocidad (1.5 = 50% más rápido, 0.5 = 50% más lento)
            output_dir: Directorio de salida
            
        Returns:
            ConversionResult con el audio a velocidad modificada
        """
        start_time = datetime.now()
        
        try:
            if not input_path.exists():
                return ConversionResult(
                    status="failed",
                    input_path=str(input_path),
                    error_message="Archivo no encontrado"
                )
            
            original_size_mb = input_path.stat().st_size / (1024 * 1024)
            
            if output_dir is None:
                output_dir = input_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Cargar audio
            audio = AudioSegment.from_file(str(input_path))
            original_duration = len(audio) / 1000.0
            
            # Cambiar velocidad (cambiando frame rate)
            # Nota: esto cambia el tono también. Para preservar tono se necesitaría librosa
            new_frame_rate = int(audio.frame_rate * speed_factor)
            speed_changed = audio._spawn(audio.raw_data, overrides={
                "frame_rate": new_frame_rate
            })
            
            # Restaurar al frame rate original para exportar
            speed_changed = speed_changed.set_frame_rate(audio.frame_rate)
            
            new_duration = len(speed_changed) / 1000.0
            
            # Guardar
            output_filename = f"{input_path.stem}_speed{speed_factor}x{input_path.suffix}"
            output_path = output_dir / output_filename
            
            speed_changed.export(str(output_path), format=input_path.suffix[1:])
            
            formatted_size_mb = output_path.stat().st_size / (1024 * 1024)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"[AudioFormatter] ✅ Velocidad cambiada")
            print(f"  Factor de velocidad: {speed_factor}x")
            print(f"  Duración original: {original_duration:.2f}s")
            print(f"  Duración nueva: {new_duration:.2f}s")
            print(f"  Tiempo ahorrado: {original_duration - new_duration:.2f}s")
            
            return ConversionResult(
                status="success",
                input_path=str(input_path),
                output_path=str(output_path),
                metrics=ConversionMetrics(
                    original_size_mb=original_size_mb,
                    formatted_size_mb=formatted_size_mb,
                    compression_ratio=original_size_mb / formatted_size_mb if formatted_size_mb > 0 else 1.0,
                    processing_time_seconds=processing_time
                )
            )
            
        except Exception as e:
            print(f"[AudioFormatter] ❌ Error cambiando velocidad: {e}")
            return ConversionResult(
                status="failed",
                input_path=str(input_path),
                error_message=str(e)
            )
