"""
Riva Client Module - Dependency Inversion Principle
Abstracts Riva SDK behind interfaces for easier testing and swapping
"""
import sys
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
            auth = Auth(
                uri=self.config.server,
                use_ssl=True,
                metadata_args=[
                    ["function-id", self.config.function_id],
                    ["authorization", f"Bearer {self.config.api_key}"]
                ]
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
        language: str = "es"
    ) -> str:
        """
        Transcribe complete audio data (offline mode)
        
        Args:
            audio_data: Audio data in WAV format
            language: Language code
            
        Returns:
            Complete transcription text
        """
        config = RecognitionConfig(
            language_code=language,
            max_alternatives=1,
            enable_automatic_punctuation=True,
            verbatim_transcripts=True,
            audio_channel_count=1,
        )
        
        # Add audio specs from WAV data
        riva.client.add_audio_file_specs_to_config(config, audio_data)
        
        response = self.asr_service.offline_recognize(audio_data, config)
        
        if response.results:
            transcript = " ".join([
                alt.transcript 
                for result in response.results 
                for alt in result.alternatives
            ])
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
