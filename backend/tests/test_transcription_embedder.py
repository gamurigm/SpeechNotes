import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

_module_name = "src.database.vector_store"
_saved_module = sys.modules.get(_module_name)
_vector_module = ModuleType(_module_name)
_vector_module.VectorStore = MagicMock
sys.modules[_module_name] = _vector_module
embedder_module = importlib.import_module("src.agent.transcription_embedder")
if _saved_module is None:
    sys.modules.pop(_module_name, None)
else:
    sys.modules[_module_name] = _saved_module
from src.agent.transcription_embedder import TranscriptionEmbedder


def _segment(index):
    return {
        "_id": index,
        "transcription_id": f"trans-{index}",
        "timestamp": index * 1.5,
        "sequence": index,
        "topic_title": "Topic" if index % 2 else None,
        "content": f"Content {index}",
    }


def test_constructor_builds_collaborators(monkeypatch):
    db = MagicMock()
    store = MagicMock()
    client = MagicMock()
    monkeypatch.setattr(embedder_module, "MongoManager", MagicMock(return_value=db))
    monkeypatch.setattr(embedder_module, "VectorStore", MagicMock(return_value=store))
    monkeypatch.setattr(embedder_module, "EmbeddingClient", MagicMock(return_value=client))

    service = TranscriptionEmbedder()

    assert service.db is db
    assert service.vector_store is store
    assert service.embedding_client is client


def test_embed_pending_returns_zero_when_nothing_is_pending(capsys):
    service = object.__new__(TranscriptionEmbedder)
    service.db = MagicMock()
    service.db.segments.find.return_value = []
    service._process_batch = MagicMock()

    assert service.embed_pending() == 0
    service._process_batch.assert_not_called()
    assert "No pending segments" in capsys.readouterr().out


def test_embed_pending_processes_in_batches_of_fifty():
    service = object.__new__(TranscriptionEmbedder)
    service.db = MagicMock()
    pending = [_segment(index) for index in range(55)]
    service.db.segments.find.return_value = pending
    service._process_batch = MagicMock()

    assert service.embed_pending() == 55
    assert [len(call.args[0]) for call in service._process_batch.call_args_list] == [50, 5]
    service.db.segments.find.assert_called_once_with(
        {"embedded": {"$ne": True}, "topic_title": {"$ne": None}}
    )


def test_process_batch_embeds_stores_and_marks_segments():
    service = object.__new__(TranscriptionEmbedder)
    service.db = MagicMock()
    service.vector_store = MagicMock()
    service.embedding_client = MagicMock()
    service.embedding_client.get_embeddings.return_value = [[0.1], [0.2]]
    batch = [_segment(1), _segment(2)]

    service._process_batch(batch)

    texts = ["Topic: Content 1", "None: Content 2"]
    service.embedding_client.get_embeddings.assert_called_once_with(texts, input_type="passage")
    service.vector_store.add_documents.assert_called_once_with(
        ids=["1", "2"],
        documents=texts,
        embeddings=[[0.1], [0.2]],
        metadatas=[
            {"transcription_id": "trans-1", "timestamp": 1.5, "topic": "Topic", "sequence": 1},
            {"transcription_id": "trans-2", "timestamp": 3.0, "topic": None, "sequence": 2},
        ],
    )
    service.db.segments.update_many.assert_called_once_with(
        {"_id": {"$in": [1, 2]}}, {"$set": {"embedded": True}}
    )


def test_process_batch_logs_failure_without_marking_embedded(capsys):
    service = object.__new__(TranscriptionEmbedder)
    service.db = MagicMock()
    service.vector_store = MagicMock()
    service.embedding_client = MagicMock()
    service.embedding_client.get_embeddings.side_effect = RuntimeError("API unavailable")

    service._process_batch([_segment(1)])

    service.vector_store.add_documents.assert_not_called()
    service.db.segments.update_many.assert_not_called()
    assert "Failed to process batch" in capsys.readouterr().out
