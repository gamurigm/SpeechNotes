"""Audio module"""
from .capture import (
    AudioConfig,
    AudioRecorder,
    MicrophoneStream,
    ContinuousRecorder,
    VADRecorder,
    BackgroundRecorder,
    VADConfig,
    MicrophoneCalibrator
)
from .factory import (
    RecorderType,
    RecorderFactory,
    MicrophoneStreamRecorderFactory,
    VADRecorderFactory,
    ContinuousRecorderFactory,
    BackgroundRecorderFactory,
    AudioRecorderFactoryProvider
)

__all__ = [
    # Capture classes
    'AudioConfig',
    'AudioRecorder',
    'MicrophoneStream',
    'ContinuousRecorder',
    'VADRecorder',
    'BackgroundRecorder',
    'VADConfig',
    'MicrophoneCalibrator',
    # Factory classes
    'RecorderType',
    'RecorderFactory',
    'MicrophoneStreamRecorderFactory',
    'VADRecorderFactory',
    'ContinuousRecorderFactory',
    'BackgroundRecorderFactory',
    'AudioRecorderFactoryProvider',
]
