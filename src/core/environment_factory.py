"""
Transcription Environment Factory - Abstract Factory Pattern
Provides interfaces for creating families of related or dependent objects
without specifying their concrete classes.

Implementation: TranscriptionEnvironmentFactory
Located: src/core/environment_factory.py

The system operates in complete "environments" that require compatible components.
For example, a "Riva Live" environment needs a Riva transcriptor and microphone recorder.
A "Local Batch" environment needs a Whisper local transcriptor and file reader.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any

from .config import ConfigManager, RivaConfig
from .riva_client import RivaTranscriber
from ..audio.capture import AudioConfig, VADConfig, AudioRecorder
from ..audio.factory import (
    AudioRecorderFactoryProvider,
    RecorderType
)
from ..transcription.formatters import (
    OutputFormatter,
    MarkdownFormatter,
    SegmentedMarkdownFormatter
)


class EnvironmentType(Enum):
    """Enumeration of available transcription environments"""
    RIVA_LIVE = "riva_live"
    LOCAL_BATCH = "local_batch"


class TranscriptionEnvironmentFactory(ABC):
    """
    Abstract Factory Pattern Implementation
    
    Propósito: Proporcionar una interfaz para crear familias de objetos 
    relacionados o dependientes sin especificar sus clases concretas.
    
    This factory creates complete "families" of components:
    - Transcriber (how to convert audio to text)
    - Recorder (how to capture audio)
    - Formatter (how to output the transcription)
    """
    
    @abstractmethod
    def create_transcriber(self) -> Any:
        """
        Create the appropriate transcriber for this environment
        
        Returns:
            Transcriber instance (e.g., RivaTranscriber, WhisperTranscriber)
        """
        pass
    
    @abstractmethod
    def create_recorder(
        self,
        recorder_type: RecorderType,
        audio_config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ) -> AudioRecorder:
        """
        Create the appropriate recorder for this environment
        
        Args:
            recorder_type: Type of recorder needed
            audio_config: Optional audio configuration
            vad_config: Optional VAD configuration
            
        Returns:
            AudioRecorder instance
        """
        pass
    
    @abstractmethod
    def create_formatter(self) -> OutputFormatter:
        """
        Create the appropriate formatter for this environment
        
        Returns:
            OutputFormatter instance
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this environment"""
        pass


class RivaLiveFactory(TranscriptionEnvironmentFactory):
    """
    Concrete factory for "Riva Live" environment
    
    This environment uses:
    - RivaTranscriber for cloud-based speech-to-text
    - MicrophoneStream/VADRecorder for real-time audio capture
    - SegmentedMarkdownFormatter for output
    """
    
    def __init__(self):
        """Initialize Riva Live factory"""
        self.config_manager = ConfigManager()
        self._transcriber: Optional[RivaTranscriber] = None
    
    def create_transcriber(self) -> RivaTranscriber:
        """
        Create Riva transcriber instance
        
        Uses the singleton ConfigManager to get Riva configuration.
        Lazy initialization to avoid connection overhead.
        
        Returns:
            RivaTranscriber instance
        """
        if self._transcriber is None:
            riva_config = self.config_manager.get_riva_config()
            self._transcriber = RivaTranscriber(riva_config)
        return self._transcriber
    
    def create_recorder(
        self,
        recorder_type: RecorderType,
        audio_config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ) -> AudioRecorder:
        """
        Create the appropriate recorder for Riva Live environment
        
        In Riva Live, we support:
        - VAD (Voice Activity Detection) for real-time transcription
        - CONTINUOUS for fixed-duration chunks
        - BACKGROUND for session recording
        
        Args:
            recorder_type: Type of recorder needed
            audio_config: Optional audio configuration
            vad_config: Optional VAD configuration
            
        Returns:
            AudioRecorder instance
        """
        return AudioRecorderFactoryProvider.create_recorder(
            recorder_type,
            config=audio_config,
            vad_config=vad_config
        )
    
    def create_formatter(self) -> OutputFormatter:
        """
        Create segmented markdown formatter for Riva Live
        
        Returns:
            SegmentedMarkdownFormatter for displaying real-time transcription
        """
        return SegmentedMarkdownFormatter()
    
    def get_name(self) -> str:
        """Get environment name"""
        return "Riva Live Real-time Transcription"


class LocalBatchFactory(TranscriptionEnvironmentFactory):
    """
    Concrete factory for "Local Batch" environment
    
    This environment uses:
    - WhisperTranscriber (or similar local transcriber) for offline speech-to-text
    - FileRecorder for batch audio file processing
    - MarkdownFormatter for output
    
    Note: Implementation of WhisperTranscriber is left for future expansion
    """
    
    def __init__(self):
        """Initialize Local Batch factory"""
        self._transcriber: Optional[Any] = None
    
    def create_transcriber(self) -> Any:
        """
        Create local transcriber instance (WhisperTranscriber)
        
        Returns:
            Transcriber instance for local, offline transcription
        """
        # NOTE: This is a placeholder for LocalBatch environment
        # To implement: Create WhisperTranscriber class that wraps OpenAI's Whisper
        # or another local speech-to-text engine for offline processing
        raise NotImplementedError(
            "LocalBatch transcriber not yet implemented. "
            "Consider implementing WhisperTranscriber for local, offline transcription."
        )
    
    def create_recorder(
        self,
        recorder_type: RecorderType,
        audio_config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ) -> AudioRecorder:
        """
        Create the appropriate recorder for Local Batch environment
        
        Args:
            recorder_type: Type of recorder needed
            audio_config: Optional audio configuration
            vad_config: Optional VAD configuration
            
        Returns:
            AudioRecorder instance
        """
        return AudioRecorderFactoryProvider.create_recorder(
            recorder_type,
            config=audio_config,
            vad_config=vad_config
        )
    
    def create_formatter(self) -> OutputFormatter:
        """
        Create markdown formatter for Local Batch
        
        Returns:
            MarkdownFormatter for batch output
        """
        return MarkdownFormatter()
    
    def get_name(self) -> str:
        """Get environment name"""
        return "Local Batch Processing"


class TranscriptionEnvironmentFactoryProvider:
    """
    Provider class for creating TranscriptionEnvironmentFactory instances
    
    This provider acts as a registry and factory for environment factories.
    It follows the Registry pattern to manage factory creation.
    """
    
    _factories: Dict[EnvironmentType, TranscriptionEnvironmentFactory] = {}
    
    @classmethod
    def create_environment(
        cls,
        environment_type: EnvironmentType
    ) -> TranscriptionEnvironmentFactory:
        """
        Create or retrieve a TranscriptionEnvironmentFactory
        
        Args:
            environment_type: Type of environment to create
            
        Returns:
            TranscriptionEnvironmentFactory instance
            
        Raises:
            ValueError: If environment type is not supported
        """
        if environment_type not in cls._factories:
            if environment_type == EnvironmentType.RIVA_LIVE:
                cls._factories[environment_type] = RivaLiveFactory()
            elif environment_type == EnvironmentType.LOCAL_BATCH:
                cls._factories[environment_type] = LocalBatchFactory()
            else:
                raise ValueError(f"Unknown environment type: {environment_type}")
        
        return cls._factories[environment_type]
    
    @classmethod
    def get_riva_live(cls) -> TranscriptionEnvironmentFactory:
        """
        Convenience method to get Riva Live environment
        
        Returns:
            RivaLiveFactory instance
        """
        return cls.create_environment(EnvironmentType.RIVA_LIVE)
    
    @classmethod
    def get_local_batch(cls) -> TranscriptionEnvironmentFactory:
        """
        Convenience method to get Local Batch environment
        
        Returns:
            LocalBatchFactory instance
        """
        return cls.create_environment(EnvironmentType.LOCAL_BATCH)
    
    @classmethod
    def reset(cls):
        """
        Reset all cached factories (useful for testing)
        """
        cls._factories.clear()
