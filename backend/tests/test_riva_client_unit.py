import importlib.util
import asyncio
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


class RecognitionConfig:
    def __init__(self, **kwargs):
        self.encoding = kwargs.pop("encoding", None)
        for key, value in kwargs.items():
            setattr(self, key, value)


class StreamingRecognitionConfig:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class RpcError(Exception):
    def __init__(self, status):
        super().__init__(str(status))
        self._status = status

    def code(self):
        return self._status


riva_package = ModuleType("riva")
riva_client = ModuleType("riva.client")
riva_client.Auth = MagicMock(name="Auth")
riva_client.ASRService = MagicMock(name="ASRService")
riva_client.AudioEncoding = SimpleNamespace(LINEAR_PCM="linear-pcm")
riva_client.StreamingRecognitionConfig = StreamingRecognitionConfig
riva_client.RecognitionConfig = RecognitionConfig
riva_client.add_word_boosting_to_config = MagicMock()
riva_client.add_audio_file_specs_to_config = MagicMock()
riva_package.client = riva_client
sys.modules["riva"] = riva_package
sys.modules["riva.client"] = riva_client

grpc = ModuleType("grpc")
grpc.RpcError = RpcError
grpc.StatusCode = SimpleNamespace(UNAVAILABLE="unavailable", INTERNAL="internal")
sys.modules["grpc"] = grpc

# Load the real implementation under a private package-qualified name. Other
# unit tests may install a type-only src.core.riva_client stub during collection.
source = Path(__file__).resolve().parents[2] / "src" / "core" / "riva_client.py"
spec = importlib.util.spec_from_file_location("src.core.riva_client_qa", source)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _config():
    return SimpleNamespace(server="riva.test:443", function_id="fn", api_key="secret")


def _response(text=None, final=True, results=True, alternatives=True):
    if not results:
        return SimpleNamespace(results=[])
    alts = [] if not alternatives else [SimpleNamespace(transcript=text)]
    return SimpleNamespace(results=[SimpleNamespace(alternatives=alts, is_final=final)])


def test_asr_service_is_created_lazily_and_cached():
    auth = MagicMock(name="auth")
    service = MagicMock(name="service")
    module.Auth.reset_mock()
    module.ASRService.reset_mock()
    module.Auth.return_value = auth
    module.ASRService.return_value = service
    transcriber = module.RivaTranscriber(_config())

    assert transcriber.asr_service is service
    assert transcriber.asr_service is service
    module.Auth.assert_called_once()
    kwargs = module.Auth.call_args.kwargs
    assert kwargs["uri"] == "riva.test:443"
    assert ["authorization", "Bearer secret"] in kwargs["metadata_args"]
    assert ("grpc.max_send_message_length", 50 * 1024 * 1024) in kwargs["options"]
    module.ASRService.assert_called_once_with(auth)


def test_streaming_transcribe_yields_valid_results_and_skips_empty():
    service = MagicMock()
    service.streaming_response_generator.return_value = [
        _response(results=False),
        _response(alternatives=False),
        _response("parcial", False),
        _response("final", True),
    ]
    transcriber = module.RivaTranscriber(_config())
    transcriber._asr_service = service
    module.riva.client.add_word_boosting_to_config.reset_mock()

    assert list(transcriber.streaming_transcribe([b"a"], "en", 8000, False)) == [
        ("parcial", False), ("final", True)
    ]
    config = service.streaming_response_generator.call_args.kwargs["streaming_config"]
    assert config.interim_results is False
    assert config.config.sample_rate_hertz == 8000
    assert config.config.language_code == "en"
    module.riva.client.add_word_boosting_to_config.assert_called_once()


def _offline(text, *, specs_error=False):
    service = MagicMock()
    service.offline_recognize.return_value = _response(text)
    transcriber = module.RivaTranscriber(_config())
    transcriber._asr_service = service
    module.riva.client.add_audio_file_specs_to_config.reset_mock()
    module.riva.client.add_audio_file_specs_to_config.side_effect = (
        ValueError("not wav") if specs_error else None
    )
    result = transcriber.offline_transcribe(b"pcm", "es", 1)
    config = service.offline_recognize.call_args.args[1]
    return result, config


def test_offline_transcribe_valid_text_and_raw_pcm_fallback():
    result, config = _offline("  Esta es una clase válida.  ", specs_error=True)
    assert result == "Esta es una clase válida."
    assert config.encoding == "linear-pcm"
    assert config.sample_rate_hertz == 16000
    assert config.audio_channel_count == 1


@pytest.mark.parametrize("text", [
    "Gracias por ver el video",
    "Gracias amigo",
    "sí sí sí sí sí clase",
    "x",
    "aaaa",
])
def test_offline_transcribe_filters_hallucinations(text):
    result, _ = _offline(text)
    assert result == ""


@pytest.mark.parametrize("text", ["sí", "no", "Una respuesta correcta"])
def test_offline_transcribe_allows_short_and_normal_valid_text(text):
    result, _ = _offline(text)
    assert result == text


def test_offline_transcribe_returns_empty_without_results():
    service = MagicMock()
    service.offline_recognize.return_value = _response(results=False)
    transcriber = module.RivaTranscriber(_config())
    transcriber._asr_service = service
    assert transcriber.offline_transcribe(b"audio", max_retries=1) == ""


def test_offline_transcribe_retries_unavailable(monkeypatch):
    first_service = MagicMock()
    first_service.offline_recognize.side_effect = RpcError(grpc.StatusCode.UNAVAILABLE)
    second_service = MagicMock()
    second_service.offline_recognize.return_value = _response("recuperado")
    module.Auth.reset_mock()
    module.ASRService.reset_mock()
    module.ASRService.side_effect = [first_service, second_service]
    monkeypatch.setattr("time.sleep", MagicMock())
    transcriber = module.RivaTranscriber(_config())
    assert transcriber.offline_transcribe(b"audio", max_retries=2) == "recuperado"
    assert module.ASRService.call_count == 2


def test_offline_transcribe_raises_after_retries_and_on_other_errors(monkeypatch):
    unavailable = MagicMock()
    unavailable.offline_recognize.side_effect = RpcError(grpc.StatusCode.UNAVAILABLE)
    transcriber = module.RivaTranscriber(_config())
    transcriber._asr_service = unavailable
    monkeypatch.setattr("time.sleep", MagicMock())
    with pytest.raises(RpcError):
        transcriber.offline_transcribe(b"audio", max_retries=1)

    internal = MagicMock()
    internal.offline_recognize.side_effect = RpcError(grpc.StatusCode.INTERNAL)
    transcriber._asr_service = internal
    with pytest.raises(RpcError):
        transcriber.offline_transcribe(b"audio", max_retries=3)

    broken = MagicMock()
    broken.offline_recognize.side_effect = ValueError("bad audio")
    transcriber._asr_service = broken
    with pytest.raises(ValueError, match="bad audio"):
        transcriber.offline_transcribe(b"audio", max_retries=3)


def test_factory_creates_transcriber():
    result = module.RivaClientFactory.create_transcriber(_config())
    assert isinstance(result, module.RivaTranscriber)


def test_transcribe_returns_empty_result_on_provider_error():
    from backend.services.nim.riva_asr_client import RivaWhisperASRClient
    from backend.services.nim.protocols import NIMConfig
    config = NIMConfig(name="test", model_id="riva", api_key="key", grpc_host="host", grpc_port=443, grpc_function_id="fn")
    transcriber = RivaWhisperASRClient(config)
    transcriber._recognize_sync = MagicMock(side_effect=RuntimeError("provider down"))
    result = asyncio.run(transcriber.transcribe(b"audio", language="es"))
    assert result.text == "" and result.language == "es" and result.confidence == 0.0
