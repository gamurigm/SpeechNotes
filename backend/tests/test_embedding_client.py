from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.llm.embedding_client as embedding_module
from src.llm.embedding_client import EmbeddingClient


@pytest.fixture(autouse=True)
def reset_embedding_client():
    EmbeddingClient._instance = None
    EmbeddingClient._initialized = False
    yield
    EmbeddingClient._instance = None
    EmbeddingClient._initialized = False


def test_embedding_client_requires_an_api_key(monkeypatch):
    config = MagicMock()
    config.get.return_value = ""
    monkeypatch.setattr(embedding_module, "ConfigService", MagicMock(return_value=config))

    with pytest.raises(ValueError, match="NVIDIA_EMBEDDING_API_KEY"):
        EmbeddingClient()


def test_embedding_client_initializes_once_and_forwards_request(monkeypatch):
    values = {
        "NVIDIA_EMBEDDING_API_KEY": "embed-key",
        "NVIDIA_BASE_URL": "https://example.test/v1",
    }
    config = MagicMock()
    config.get.side_effect = lambda key, default="": values.get(key, default)
    api = MagicMock()
    api.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[1.0, 2.0]), SimpleNamespace(embedding=[3.0])]
    )
    openai_cls = MagicMock(return_value=api)
    monkeypatch.setattr(embedding_module, "ConfigService", MagicMock(return_value=config))
    monkeypatch.setattr(embedding_module, "OpenAI", openai_cls)

    client = EmbeddingClient()
    same_client = EmbeddingClient()
    embeddings = client.get_embeddings(["one", "two"], input_type="passage")

    assert same_client is client
    assert embeddings == [[1.0, 2.0], [3.0]]
    openai_cls.assert_called_once_with(base_url="https://example.test/v1", api_key="embed-key")
    api.embeddings.create.assert_called_once_with(
        input=["one", "two"],
        model="nvidia/llama-3.2-nemoretriever-300m-embed-v2",
        encoding_format="float",
        extra_body={"input_type": "passage", "truncate": "NONE"},
    )


def test_get_embedding_returns_first_vector(monkeypatch):
    client = object.__new__(EmbeddingClient)
    client.get_embeddings = MagicMock(return_value=[[0.25, 0.75]])

    assert client.get_embedding("hello") == [0.25, 0.75]
    client.get_embeddings.assert_called_once_with(["hello"], "query")


def test_embedding_api_errors_are_not_hidden(capsys):
    client = object.__new__(EmbeddingClient)
    client.client = MagicMock()
    client.model_name = "model"
    client.client.embeddings.create.side_effect = RuntimeError("network down")

    with pytest.raises(RuntimeError, match="network down"):
        client.get_embeddings(["text"])
    assert "Failed to generate embeddings" in capsys.readouterr().out
