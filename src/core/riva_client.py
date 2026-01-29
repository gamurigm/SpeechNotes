"""
Riva Client Module - Dependency Inversion Principle
Abstracts Riva SDK behind interfaces for easier testing and swapping
"""
import sys
import re
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Generator, Protocol

# Add python-clients to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python-clients"))

from riva.client import Auth, ASRService, AudioEncoding, StreamingRecognitionConfig, RecognitionConfig
import riva.client
import riva.client.audio_io as audio_io

from ..core.config import RivaConfig


class TranscriptionService(Protocol):
    """Protocol for transcription services (DIP: depend on abstraction)"""
    
    def streaming_transcribe(self, audio_stream, language: str = "es") -> Generator[str, None, None]:
        """Stream transcription results"""
        ...
    
    def offline_transcribe(self, audio_data: bytes, language: str = "es") -> str:
        """Transcribe complete audio file"""
        ...


class RivaTranscriber:
    """
    Concrete implementation of transcription using NVIDIA Riva
    SRP: Only responsible for Riva API interactions
    """
    
    def __init__(self, config: RivaConfig):
        """
        Initialize Riva transcriber
        
        Args:
            config: Riva configuration object
        """
        self.config = config
        self._asr_service = None
    
    @property
    def asr_service(self) -> ASRService:
        """Lazy initialization of ASR service"""
        if self._asr_service is None:
            # Configure gRPC channel options with longer timeouts
            # to prevent connection timeout errors
            channel_options = [
                ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.keepalive_time_ms', 30000),  # 30 seconds
                ('grpc.keepalive_timeout_ms', 10000),  # 10 seconds
                ('grpc.keepalive_permit_without_calls', 1),
                ('grpc.http2.max_pings_without_data', 0),
                # Increase timeouts to 120 seconds for slower connections
                ('grpc.http2.min_time_between_pings_ms', 10000),
            ]
            
            auth = Auth(
                uri=self.config.server,
                use_ssl=True,
                metadata_args=[
                    ["function-id", self.config.function_id],
                    ["authorization", f"Bearer {self.config.api_key}"]
                ],
                options=channel_options
            )
            self._asr_service = ASRService(auth)
        return self._asr_service
    
    def streaming_transcribe(
        self, 
        audio_stream, 
        language: str = "es",
        sample_rate: int = 16000,
        interim_results: bool = True
    ) -> Generator[tuple[str, bool], None, None]:
        """
        Stream transcription from audio stream
        
        Args:
            audio_stream: Audio input stream
            language: Language code
            sample_rate: Sample rate in Hz
            interim_results: Whether to return interim results
            
        Yields:
            Tuple of (transcript, is_final)
        """
        config = StreamingRecognitionConfig(
            config=RecognitionConfig(
                encoding=AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=sample_rate,
                language_code=language,
                max_alternatives=1,
                enable_automatic_punctuation=True,
                verbatim_transcripts=True,
                audio_channel_count=1,
            ),
            interim_results=interim_results,
        )
        
        responses = self.asr_service.streaming_response_generator(
            audio_chunks=audio_stream,
            streaming_config=config
        )
        
        for response in responses:
            if not response.results:
                continue
            
            for result in response.results:
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript
                yield transcript, result.is_final
    
    def offline_transcribe(
        self, 
        audio_data: bytes, 
        language: str = "es",
        max_retries: int = 3
    ) -> str:
        """
        Transcribe complete audio data (offline mode) with automatic retry
        
        Args:
            audio_data: Audio data in WAV format or raw PCM
            language: Language code
            max_retries: Maximum number of retry attempts on timeout
            
        Returns:
            Complete transcription text
        """
        import grpc
        import time
        
        last_error = None
        for attempt in range(max_retries):
            try:
                config = RecognitionConfig(
                    language_code=language,
                    max_alternatives=1,
                    enable_automatic_punctuation=True,
                    verbatim_transcripts=True,
                    audio_channel_count=1,
                )
                
                # Try to detect WAV header
                try:
                    riva.client.add_audio_file_specs_to_config(config, audio_data)
                except Exception:
                    # Ignore errors if not a WAV file
                    pass
                    
                # If encoding is still not set (e.g. raw PCM), default to LINEAR_PCM/16k
                if not config.encoding:
                    config.encoding = AudioEncoding.LINEAR_PCM
                    config.sample_rate_hertz = 16000
                    config.audio_channel_count = 1
                
                response = self.asr_service.offline_recognize(audio_data, config)
                
                # If successful, break out of retry loop
                break
                
            except grpc.RpcError as e:
                last_error = e
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        print(f"\n   ⚠️  Conexión perdida, reintentando en {wait_time}s... (intento {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        # Reset the service to force reconnection
                        self._asr_service = None
                        continue
                    else:
                        print(f"\n   ❌ Error: Servicio de Riva no disponible después de {max_retries} intentos")
                        print(f"      Verifica que el servidor esté corriendo: {self.config.server}")
                        raise
                else:
                    # For other gRPC errors, don't retry
                    raise
            except Exception as e:
                # For non-gRPC errors, don't retry
                last_error = e
                raise
        
        if last_error:
            raise last_error
        
        if response.results:
            transcript = " ".join([
                alt.transcript 
                for result in response.results 
                for alt in result.alternatives
            ])
            
            # ========== HALLUCINATION FILTER ==========
            # Filter out common ASR hallucinations that occur during silence or low audio
            
            # Normalize for checking: lowercase, remove punctuation
            cleaned = transcript.strip().lower()
            cleaned = re.sub(r'[!¡?¿.,;:\-–—]', '', cleaned).strip()
            
            # 1. Common hallucination phrases (exact or prefix match)
            hallucinations = [
                # Spanish common hallucinations (Removed valid greetings/common words)
                "gracias por ver", "gracias por ver el video",
                "gracias por ver el vídeo", "gracias por vernos",
                "suscríbete", "suscríbete al canal", "dale like",
                "subtítulos por", "subtítulos realizados por",
                "subtítulos", "transcripción",
                "traducido por", "traducción por",
                "esto es un regalo", "es un regalo",
                "música", "aplausos", "risas",
                # English common hallucinations
                "thank you", "thank you for watching",
                "thanks for watching", "subscribe",
                "subtitles", "translated by",
                "amara.org", "captions by",
                # Generic silence fillers (Removed "bien", "ok")
                "uh", "um", "eh", "ah",
            ]
            
            # Check exact match or prefix
            for h in hallucinations:
                h_clean = re.sub(r'[!¡?¿.,;:\-–—]', '', h).strip()
                if cleaned == h_clean:
                    print(f"[Hallucination Filter] Blocked exact match: '{transcript}'")
                    return ""
                if cleaned.startswith(h_clean) and len(cleaned) < len(h_clean) + 10:
                    print(f"[Hallucination Filter] Blocked prefix match: '{transcript}'")
                    return ""
            
            # 2. Detect repetitive patterns (e.g., "Sí. Sí. Sí. Sí.")
            words = re.findall(r'\b\w+\b', cleaned)
            if len(words) >= 4:  # Increased form 3 to 4 to allow "Si si si"
                # Check if a single word is repeated too many times
                from collections import Counter
                word_counts = Counter(words)
                most_common_word, most_common_count = word_counts.most_common(1)[0]
                
                # If one word makes up more than 80% of all words (relaxed from 60%)
                if most_common_count / len(words) > 0.8 and len(words) >= 4:
                    print(f"[Hallucination Filter] Blocked repetitive pattern: '{transcript}'")
                    return ""
            
            # 3. Filter very short transcripts (likely noise) - Relaxed
            if len(cleaned) < 2:  # Allow 2 chars (e.g. "Si", "No", "Ir")
                print(f"[Hallucination Filter] Blocked too short: '{transcript}'")
                return ""
            
            # 4. Filter if only contains single repeated character
            if len(set(cleaned.replace(' ', ''))) <= 1: # Allow "aba" (a, b) -> 2 chars. Relaxed from 2 to 1
                print(f"[Hallucination Filter] Blocked single char repetition: '{transcript}'")
                return ""

            return transcript.strip()
        
        return ""


class RivaClientFactory:
    """
    Factory for creating Riva clients
    Factory Pattern: Encapsulates client creation logic
    """
    
    @staticmethod
    def create_transcriber(config: RivaConfig) -> RivaTranscriber:
        """
        Create a Riva transcriber instance
        
        Args:
            config: Riva configuration
            
        Returns:
            Configured RivaTranscriber instance
        """
        return RivaTranscriber(config)
