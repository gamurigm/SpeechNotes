"""Speech transcription package"""
__version__ = "2.0.0"

from .core import ConfigManager, RivaConfig
from .core.riva_client import RivaClientFactory, RivaTranscriber
from .audio import (
    AudioConfig,
    MicrophoneStream,
    ContinuousRecorder,
    VADRecorder,
    VADConfig,
    MicrophoneCalibrator
)
from .transcription import (
    FormatterFactory,
    OutputWriter,
    TranscriptionService
)

__all__ = [
    'ConfigManager',
    'RivaConfig',
    'RivaClientFactory',
    'RivaTranscriber',
    'AudioConfig',
    'MicrophoneStream',
    'ContinuousRecorder',
    'VADRecorder',
    'VADConfig',
    'MicrophoneCalibrator',
    'FormatterFactory',
    'OutputWriter',
    'TranscriptionService'
]
