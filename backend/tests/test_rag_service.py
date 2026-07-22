import asyncio
import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

_module_name = "src.agent.rag_agent"
_saved_module = sys.modules.get(_module_name)
_fake_module = ModuleType(_module_name)
_fake_module.RagAgent = MagicMock
sys.modules[_module_name] = _fake_module
rag_module = importlib.import_module("backend.services.knowledge.rag_service")
if _saved_module is None:
    sys.modules.pop(_module_name, None)
else:
    sys.modules[_module_name] = _saved_module

RagService = rag_module.RagService


def test_constructor_handles_agent_success_and_failure(monkeypatch):
    agent = MagicMock()
    monkeypatch.setattr(rag_module, "RagAgent", MagicMock(return_value=agent))
    assert RagService().agent is agent

    monkeypatch.setattr(rag_module, "RagAgent", MagicMock(side_effect=RuntimeError("init failed")))
    assert RagService().agent is None


def test_chat_handles_unavailable_success_and_error():
    service = object.__new__(RagService)
    service.agent = None
    assert service.chat("hello")["sources"] == []

    service.agent = MagicMock()
    service.agent.chat.return_value = "answer"
    assert service.chat("hello") == {"answer": "answer", "sources": []}

    service.agent.chat.side_effect = RuntimeError("model failed")
    assert service.chat("hello") == {
        "answer": "Error generating response: model failed",
        "sources": [],
    }


async def _collect_stream(service, query="hello", active_file=None):
    return [chunk async for chunk in service.chat_stream(query, active_file)]


def test_chat_stream_handles_unavailable_success_and_error():
    service = object.__new__(RagService)
    service.agent = None
    assert "no está disponible" in asyncio.run(_collect_stream(service))[0]

    service.agent = MagicMock()
    service.agent.chat_stream.return_value = iter(["one", "two"])
    assert asyncio.run(_collect_stream(service, active_file="note.md")) == ["one", "two"]
    service.agent.chat_stream.assert_called_once_with("hello", active_file="note.md")

    service.agent.chat_stream.side_effect = RuntimeError("stream failed")
    assert asyncio.run(_collect_stream(service)) == ["Error in stream: stream failed"]


def test_search_file_handles_unavailable_success_and_error():
    service = object.__new__(RagService)
    service.agent = None
    assert service.search_file("query", "note.md") == {
        "context": None,
        "error": "RAG agent not initialized",
    }

    service.agent = MagicMock()
    service.agent.search_file_context.return_value = "matching context"
    assert service.search_file("query", "note.md") == {"context": "matching context"}

    service.agent.search_file_context.side_effect = RuntimeError("search failed")
    assert service.search_file("query", "note.md") == {
        "context": None,
        "error": "search failed",
    }
