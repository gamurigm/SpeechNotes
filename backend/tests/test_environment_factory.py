import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

_dependency_names = ("src.core.riva_client", "src.audio.capture", "src.audio.factory")
_saved_modules = {name: sys.modules.get(name) for name in _dependency_names}

_riva_module = ModuleType("src.core.riva_client")
_riva_module.RivaTranscriber = MagicMock
_capture_module = ModuleType("src.audio.capture")
for _name in ("AudioConfig", "VADConfig", "AudioRecorder"):
    setattr(_capture_module, _name, type(_name, (), {}))
_factory_module = ModuleType("src.audio.factory")
_factory_module.AudioRecorderFactoryProvider = MagicMock()
_factory_module.RecorderType = type("RecorderType", (), {})
sys.modules.update(
    {
        "src.core.riva_client": _riva_module,
        "src.audio.capture": _capture_module,
        "src.audio.factory": _factory_module,
    }
)
factory_module = importlib.import_module("src.core.environment_factory")
for _name, _saved in _saved_modules.items():
    if _saved is None:
        sys.modules.pop(_name, None)
    else:
        sys.modules[_name] = _saved
from src.core.environment_factory import (
    EnvironmentType,
    LocalBatchFactory,
    RivaLiveFactory,
    TranscriptionEnvironmentFactoryProvider,
)


@pytest.fixture(autouse=True)
def reset_provider():
    TranscriptionEnvironmentFactoryProvider.reset()
    yield
    TranscriptionEnvironmentFactoryProvider.reset()


def test_riva_factory_lazily_creates_and_caches_transcriber(monkeypatch):
    config = MagicMock(name="config")
    manager = MagicMock()
    manager.get_riva_config.return_value = config
    transcriber = MagicMock(name="transcriber")
    transcriber_cls = MagicMock(return_value=transcriber)
    monkeypatch.setattr(factory_module, "ConfigManager", MagicMock(return_value=manager))
    monkeypatch.setattr(factory_module, "RivaTranscriber", transcriber_cls)

    environment = RivaLiveFactory()

    assert environment.create_transcriber() is transcriber
    assert environment.create_transcriber() is transcriber
    manager.get_riva_config.assert_called_once_with()
    transcriber_cls.assert_called_once_with(config)
    assert environment.get_name() == "Riva Live Real-time Transcription"
    assert isinstance(environment.create_formatter(), factory_module.SegmentedMarkdownFormatter)


def test_factories_delegate_recorder_creation(monkeypatch):
    recorder = MagicMock(name="recorder")
    create_recorder = MagicMock(return_value=recorder)
    monkeypatch.setattr(
        factory_module.AudioRecorderFactoryProvider,
        "create_recorder",
        create_recorder,
    )
    monkeypatch.setattr(factory_module, "ConfigManager", MagicMock())
    recorder_type = MagicMock(name="recorder_type")
    audio_config = MagicMock(name="audio_config")
    vad_config = MagicMock(name="vad_config")

    assert RivaLiveFactory().create_recorder(recorder_type, audio_config, vad_config) is recorder
    assert LocalBatchFactory().create_recorder(recorder_type, audio_config, vad_config) is recorder
    assert create_recorder.call_count == 2
    create_recorder.assert_called_with(
        recorder_type,
        config=audio_config,
        vad_config=vad_config,
    )


def test_local_batch_factory_contract():
    environment = LocalBatchFactory()

    with pytest.raises(NotImplementedError, match="WhisperTranscriber"):
        environment.create_transcriber()
    assert environment.get_name() == "Local Batch Processing"
    assert isinstance(environment.create_formatter(), factory_module.MarkdownFormatter)


def test_provider_caches_each_supported_environment(monkeypatch):
    monkeypatch.setattr(factory_module, "ConfigManager", MagicMock())

    riva = TranscriptionEnvironmentFactoryProvider.get_riva_live()
    local = TranscriptionEnvironmentFactoryProvider.get_local_batch()

    assert isinstance(riva, RivaLiveFactory)
    assert isinstance(local, LocalBatchFactory)
    assert TranscriptionEnvironmentFactoryProvider.get_riva_live() is riva
    assert TranscriptionEnvironmentFactoryProvider.get_local_batch() is local

    TranscriptionEnvironmentFactoryProvider.reset()
    assert TranscriptionEnvironmentFactoryProvider._factories == {}


def test_provider_rejects_unknown_environment():
    with pytest.raises(ValueError, match="Unknown environment type"):
        TranscriptionEnvironmentFactoryProvider.create_environment(object())


def test_environment_enum_values_are_stable():
    assert EnvironmentType.RIVA_LIVE.value == "riva_live"
    assert EnvironmentType.LOCAL_BATCH.value == "local_batch"
