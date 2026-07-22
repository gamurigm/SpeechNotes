"""Speech transcription package.

Public components are loaded lazily so importing a focused subpackage such as
``src.database`` does not initialize optional audio or transcription stacks.
"""

from importlib import import_module

__version__ = "2.0.0"
_AUDIO_MODULE = ".audio"
_TRANSCRIPTION_MODULE = ".transcription"

_EXPORTS = {
    "ConfigManager": (".core", "ConfigManager"),
    "RivaConfig": (".core", "RivaConfig"),
    "RivaClientFactory": (".core.riva_client", "RivaClientFactory"),
    "RivaTranscriber": (".core.riva_client", "RivaTranscriber"),
    "AudioConfig": (_AUDIO_MODULE, "AudioConfig"),
    "MicrophoneStream": (_AUDIO_MODULE, "MicrophoneStream"),
    "ContinuousRecorder": (_AUDIO_MODULE, "ContinuousRecorder"),
    "VADRecorder": (_AUDIO_MODULE, "VADRecorder"),
    "VADConfig": (_AUDIO_MODULE, "VADConfig"),
    "MicrophoneCalibrator": (_AUDIO_MODULE, "MicrophoneCalibrator"),
    "FormatterFactory": (_TRANSCRIPTION_MODULE, "FormatterFactory"),
    "OutputWriter": (_TRANSCRIPTION_MODULE, "OutputWriter"),
    "TranscriptionService": (_TRANSCRIPTION_MODULE, "TranscriptionService"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    """Import optional public components only when requested."""
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value
