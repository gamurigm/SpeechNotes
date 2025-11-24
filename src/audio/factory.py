"""
Audio Recorder Factory - Factory Method Pattern
Creates different types of audio recorders based on the context
SRP: Each factory only knows how to create one type of recorder
OCP: Easy to extend with new recorder types
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from .capture import (
    AudioConfig,
    AudioRecorder,
    MicrophoneStream,
    VADRecorder,
    VADConfig,
    ContinuousRecorder,
    BackgroundRecorder
)


class RecorderType(Enum):
    """Enumeration of available recorder types"""
    MICROPHONE_STREAM = "microphone_stream"
    VAD = "vad"
    CONTINUOUS = "continuous"
    BACKGROUND = "background"


class RecorderFactory(ABC):
    """
    Abstract factory for creating audio recorders
    Factory Method Pattern: Defines interface for object creation
    """
    
    @abstractmethod
    def create_recorder(self, config: Optional[AudioConfig] = None) -> AudioRecorder:
        """
        Create a recorder instance
        
        Args:
            config: Optional audio configuration
            
        Returns:
            AudioRecorder instance
        """
        pass


class MicrophoneStreamRecorderFactory(RecorderFactory):
    """Factory for creating continuous microphone stream recorders"""
    
    def create_recorder(self, config: Optional[AudioConfig] = None) -> MicrophoneStream:
        """
        Create a MicrophoneStream recorder
        
        Args:
            config: Optional audio configuration
            
        Returns:
            MicrophoneStream instance for continuous streaming
        """
        return MicrophoneStream(config or AudioConfig())


class VADRecorderFactory(RecorderFactory):
    """Factory for creating Voice Activity Detection recorders"""
    
    def create_recorder(
        self,
        config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ) -> VADRecorder:
        """
        Create a VADRecorder
        
        Args:
            config: Optional audio configuration
            vad_config: Optional VAD-specific configuration
            
        Returns:
            VADRecorder instance for voice-triggered recording
        """
        audio_config = config or AudioConfig()
        vad_cfg = vad_config or VADConfig()
        return VADRecorder(audio_config, vad_cfg)


class ContinuousRecorderFactory(RecorderFactory):
    """Factory for creating continuous fixed-duration recorders"""
    
    def create_recorder(self, config: Optional[AudioConfig] = None) -> ContinuousRecorder:
        """
        Create a ContinuousRecorder
        
        Args:
            config: Optional audio configuration
            
        Returns:
            ContinuousRecorder instance for fixed-duration chunks
        """
        return ContinuousRecorder(config or AudioConfig())


class BackgroundRecorderFactory(RecorderFactory):
    """Factory for creating background recording recorders"""
    
    def create_recorder(self, config: Optional[AudioConfig] = None) -> BackgroundRecorder:
        """
        Create a BackgroundRecorder
        
        Args:
            config: Optional audio configuration
            
        Returns:
            BackgroundRecorder instance for background recording
        """
        return BackgroundRecorder(config or AudioConfig())


class AudioRecorderFactoryProvider:
    """
    Provider class that returns the appropriate factory based on recorder type
    Implements a higher-level factory pattern for factory selection
    """
    
    _factories = {
        RecorderType.MICROPHONE_STREAM: MicrophoneStreamRecorderFactory(),
        RecorderType.VAD: VADRecorderFactory(),
        RecorderType.CONTINUOUS: ContinuousRecorderFactory(),
        RecorderType.BACKGROUND: BackgroundRecorderFactory(),
    }
    
    @classmethod
    def get_factory(cls, recorder_type: RecorderType) -> RecorderFactory:
        """
        Get the appropriate factory for a given recorder type
        
        Args:
            recorder_type: The type of recorder to create
            
        Returns:
            The corresponding RecorderFactory
            
        Raises:
            ValueError: If recorder type is not supported
        """
        if recorder_type not in cls._factories:
            raise ValueError(
                f"Unsupported recorder type: {recorder_type}. "
                f"Available: {list(cls._factories.keys())}"
            )
        return cls._factories[recorder_type]
    
    @classmethod
    def create_recorder(
        cls,
        recorder_type: RecorderType,
        config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ) -> AudioRecorder:
        """
        Create a recorder of the specified type
        Convenience method that combines factory selection and creation
        
        Args:
            recorder_type: The type of recorder to create
            config: Optional audio configuration
            vad_config: Optional VAD configuration (only for VAD recorder)
            
        Returns:
            The created AudioRecorder instance
            
        Example:
            # Create a VAD recorder
            recorder = AudioRecorderFactoryProvider.create_recorder(
                RecorderType.VAD,
                config=AudioConfig(),
                vad_config=VADConfig()
            )
        """
        factory = cls.get_factory(recorder_type)
        
        # Special handling for VAD factory which needs vad_config
        if isinstance(factory, VADRecorderFactory):
            return factory.create_recorder(config, vad_config)
        else:
            return factory.create_recorder(config)
