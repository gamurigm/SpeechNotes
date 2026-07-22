import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest

if "numpy" not in sys.modules:
    sys.modules["numpy"] = MagicMock()
if "faiss" not in sys.modules:
    sys.modules["faiss"] = MagicMock()

import src.agent.vector_store as module


class Array(list):
    @property
    def shape(self):
        return (len(self), len(self[0]) if self and isinstance(self[0], (list, Array)) else len(self))


class FakeNumpy:
    float32 = "float32"

    @staticmethod
    def array(values, dtype=None):
        if values and isinstance(values[0], (int, float)):
            return Array(values)
        return Array([Array(row) for row in values])


class FakeIndex:
    def __init__(self, dimension):
        self.dimension = dimension
        self.vectors = []

    def add(self, vectors):
        self.vectors.extend(vectors)

    def search(self, query, k):
        distances = [float(i) for i in range(min(k, len(self.vectors)))]
        indexes = list(range(len(distances)))
        return [distances], [indexes]


class FakeFaiss:
    IndexFlatL2 = FakeIndex


def _store(monkeypatch, key="key"):
    monkeypatch.setattr(module, "np", FakeNumpy)
    monkeypatch.setattr(module, "faiss", FakeFaiss)
    monkeypatch.setattr(module.os, "getenv", lambda name, default=None: key if name == "NVIDIA_EMBEDDING_API_KEY" else default)
    store = module.VectorStore()
    store.client = MagicMock()
    store.client.embeddings.create.side_effect = lambda **kwargs: SimpleNamespace(
        data=[SimpleNamespace(embedding=[1.0, 2.0])]
    )
    return store


def test_vector_store_inactive_without_key(monkeypatch):
    monkeypatch.setattr(module.os, "getenv", lambda name, default=None: None if name == "NVIDIA_EMBEDDING_API_KEY" else default)
    store = module.VectorStore()
    assert store.client is None and len(store) == 0


def test_add_documents_empty_and_metadata_validation(monkeypatch):
    store = _store(monkeypatch)
    store.add_documents([])
    with pytest.raises(ValueError, match="Metadata length"):
        store.add_documents(["a"], [])


def test_add_search_threshold_and_clear(monkeypatch):
    store = _store(monkeypatch)
    store.add_documents(["first", "second"], [{"id": 1}, {"id": 2}])
    assert len(store) == 2 and store.dimension == 2
    results = store.search("query", k=5)
    assert len(results) == 2 and results[0]["document"] == "first" and results[0]["rank"] == 1
    assert store.search("query", score_threshold=2.0) == []
    store.clear()
    assert len(store) == 0 and store.index is None and store.dimension is None


def test_embedding_error_is_wrapped(monkeypatch):
    store = _store(monkeypatch)
    store.client.embeddings.create.side_effect = RuntimeError("NIM")
    with pytest.raises(RuntimeError, match="Error getting embedding.*NIM"):
        store._get_embedding("text")
