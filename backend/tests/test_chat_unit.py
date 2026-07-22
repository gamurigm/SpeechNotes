"""Unit coverage for chat context selection and streaming endpoints."""

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock
from types import ModuleType
from pydantic import BaseModel

import pytest
from unittest.mock import MagicMock

sys.modules.setdefault("pydantic_ai", MagicMock())
sys.modules.setdefault("dotenv", MagicMock())
if "services.agents.pydantic_agent" not in sys.modules:
    services = ModuleType("services")
    services.__path__ = []
    agents = ModuleType("services.agents")
    agents.__path__ = []
    agent_module = ModuleType("services.agents.pydantic_agent")
    class _DocumentContext(BaseModel):
        doc_id: str
        filename: str | None = None
        title: str | None = None
        content: str
        content_type: str
    async def _stream(*args, **kwargs):
        if False:
            yield ""
    agent_module.DocumentContext = _DocumentContext
    agent_module.chat_stream_direct = _stream
    agent_module.chat_stream_with_document = _stream
    sys.modules.update({"services": services, "services.agents": agents,
                        "services.agents.pydantic_agent": agent_module})

import backend.routers.chat as module


def _doc(**values):
    base = {"_id": "d1", "filename": "note.md", "raw_content": "# Title\nhello"}
    base.update(values)
    return base


def test_load_document_context_content_variants(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(module, "db", db)
    db.transcriptions.find_one.side_effect = [None, _doc(formatted_content="formatted", raw_content="")]
    context = module.load_document_context("note.md")
    assert context.content == "formatted" and context.content_type == "formatted"

    db.transcriptions.find_one.side_effect = [_doc(edited_content="edited", formatted_content="formatted")]
    context = module.load_document_context("d1")
    assert context.content == "edited" and context.content_type == "edited"

    db.transcriptions.find_one.side_effect = [_doc(raw_content="", formatted_content="")]
    db.segments.find.return_value.sort.return_value = [{"text": "one"}, {"text": "two"}]
    context = module.load_document_context("d1")
    assert context.content == "one\n\ntwo" and context.content_type == "segments"


def test_load_document_context_empty_and_invalid(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(module, "db", db)
    assert module.load_document_context("   ") is None
    db.transcriptions.find_one.return_value = _doc(raw_content="", formatted_content="")
    db.segments.find.return_value.sort.return_value = []
    context = module.load_document_context("d1")
    assert context.content_type == "empty"
    db.transcriptions.find_one.side_effect = RuntimeError("db")
    assert module.load_document_context("d1") is None


def test_load_by_filename_fallback_and_missing(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(module, "db", db)
    db.transcriptions.find_one.side_effect = [None, _doc()]
    monkeypatch.setattr(module, "load_document_context", lambda value: "context")
    assert module.load_document_by_filename("note.md") == "context"
    db.transcriptions.find_one.side_effect = [None, None]
    assert module.load_document_by_filename("missing.wav") is None


async def _chunks(*items):
    for item in items:
        yield item


def test_chat_stream_preloaded_content_and_no_user(monkeypatch):
    monkeypatch.setattr(module, "chat_stream_direct", lambda *args, **kwargs: _chunks("answer"))
    request = module.ChatRequest(messages=[module.Message(role="user", content="hello")], doc_content="# Doc\nlong enough content")
    response = asyncio.run(module.chat_stream(request))
    body = b"".join(asyncio.run(_collect(response.body_iterator)))
    assert b"answer" in body and b'"done": true' in body
    with pytest.raises(module.HTTPException) as exc:
        asyncio.run(module.chat_stream(module.ChatRequest(messages=[])))
    assert exc.value.status_code == 400


async def _collect(iterator):
    values = []
    async for value in iterator:
        values.append(value.encode() if isinstance(value, str) else value)
    return values


def test_chat_nonstreaming_and_index(monkeypatch):
    doc = module.DocumentContext(doc_id="d1", filename="x", title="X", content="body", content_type="raw")
    monkeypatch.setattr(module, "load_document_context", lambda _: doc)
    monkeypatch.setattr(module, "chat_stream_direct", lambda *args, **kwargs: _chunks("a", "b"))
    request = module.ChatRequest(messages=[module.Message(role="user", content="q")], doc_id="d1")
    response = asyncio.run(module.chat(request))
    assert response.answer == "ab" and response.sources[0]["doc_id"] == "d1"
    assert asyncio.run(module.trigger_indexing())["message"]
