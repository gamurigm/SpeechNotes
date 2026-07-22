from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.llm.nvidia_client as module


@pytest.fixture(autouse=True)
def reset_singleton():
    module.NvidiaInferenceClient._instance = None
    module.NvidiaInferenceClient._initialized = False
    yield
    module.NvidiaInferenceClient._instance = None
    module.NvidiaInferenceClient._initialized = False


def _completion(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def _client(create_result=None):
    client = object.__new__(module.NvidiaInferenceClient)
    client.model_name = "model"
    client.temperature = 0.2
    client.top_p = 0.7
    client.max_tokens = 100
    client.client = MagicMock()
    if create_result is not None:
        client.client.chat.completions.create.return_value = create_result
    return client


def test_initialization_reads_configuration_and_is_singleton(monkeypatch):
    values = {
        "NVIDIA_API_KEY": " nvapi-secret # comment ",
        "NVIDIA_BASE_URL": "https://example.test/v1",
        "MODEL_NAME": "qa-model",
        "TEMPERATURE": "0.4",
        "TOP_P": "0.8",
        "MAX_TOKENS": "321",
    }
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: values.get(key, default)
    openai = MagicMock()
    monkeypatch.setattr(module, "ConfigService", lambda: config)
    monkeypatch.setattr(module, "OpenAI", openai)

    first = module.NvidiaInferenceClient()
    second = module.NvidiaInferenceClient()

    assert first is second
    assert first.api_key == "nvapi-secret"
    assert (first.temperature, first.top_p, first.max_tokens) == (0.4, 0.8, 321)
    openai.assert_called_once_with(base_url="https://example.test/v1", api_key="nvapi-secret")


def test_initialization_rejects_missing_key(monkeypatch):
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: None if key == "NVIDIA_API_KEY" else default
    monkeypatch.setattr(module, "ConfigService", lambda: config)
    with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
        module.NvidiaInferenceClient()


def test_generate_builds_messages_and_honours_parameters():
    client = _client(_completion("respuesta"))
    messages = [{"role": "system", "content": "reglas"}]
    result = client.generate("hola", messages, temperature=0, top_p=1, max_tokens=5, seed=7)
    assert result == "respuesta"
    assert messages[-1] == {"role": "user", "content": "hola"}
    client.client.chat.completions.create.assert_called_once_with(
        model="model", messages=messages, temperature=0, top_p=1,
        max_tokens=5, stream=False, seed=7,
    )


def test_generate_uses_defaults_without_duplicating_prompt():
    client = _client(_completion("ok"))
    messages = [{"role": "user", "content": "hola"}]
    assert client.generate("hola", messages) == "ok"
    assert len(messages) == 1
    assert client.generate("nuevo") == "ok"


def test_generate_wraps_provider_errors():
    client = _client()
    client.client.chat.completions.create.side_effect = OSError("network")
    with pytest.raises(RuntimeError, match="Error generating.*network"):
        client.generate("hola")


def test_stream_generate_yields_only_content(monkeypatch):
    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="uno"))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="dos"))]),
    ]
    client = _client(chunks)
    monkeypatch.setattr(module.logfire, "span", lambda *args, **kwargs: nullcontext())
    messages = []
    assert list(client.stream_generate("hola", messages, temperature=0.1)) == ["uno", "dos"]
    assert messages == [{"role": "user", "content": "hola"}]
    assert client.client.chat.completions.create.call_args.kwargs["stream"] is True


def test_stream_generate_wraps_errors(monkeypatch):
    client = _client()
    client.client.chat.completions.create.side_effect = ValueError("bad stream")
    monkeypatch.setattr(module.logfire, "span", lambda *args, **kwargs: nullcontext())
    with pytest.raises(RuntimeError, match="Error streaming.*bad stream"):
        list(client.stream_generate("hola"))


def test_chat_success_and_error():
    client = _client(_completion("chat-ok"))
    messages = [{"role": "user", "content": "hola"}]
    assert client.chat(messages, temperature=0, top_p=0.5, max_tokens=9, seed=3) == "chat-ok"
    kwargs = client.client.chat.completions.create.call_args.kwargs
    assert kwargs == {"model": "model", "messages": messages, "temperature": 0,
                      "top_p": 0.5, "max_tokens": 9, "stream": False, "seed": 3}
    client.client.chat.completions.create.side_effect = RuntimeError("provider")
    with pytest.raises(RuntimeError, match="Error in chat completion.*provider"):
        client.chat(messages)
